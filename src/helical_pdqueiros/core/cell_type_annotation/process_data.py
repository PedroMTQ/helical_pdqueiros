from helical_pdqueiros.settings import LOCAL_CHUNKED_DATA_PATH, CHUNKED_DATA_PATH, CHUNKED_DATA_ERROR_PATH, PROCESSED_DATA_PATH, LOCAL_PROCESSED_DATA_PATH
from helical_pdqueiros.core.documents.data_document import DataDocument
from helical_pdqueiros.core.base_task import BaseTask
from helical_pdqueiros.core.cell_type_annotation.data_processer import CellTypeAnnotationDataProcessor
import os
from pathlib import Path
from retry import retry
import shutil
import ray
from helical.models.geneformer.geneformer_config import GeneformerConfig
import logging
from helical_pdqueiros.io.logger import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

SLEEP_TIME = int(os.getenv('SLEEP_TIME', '0'))
RAY_ENDPOINT = os.getenv('RAY_ENDPOINT', 'ray://localhost:10001')

import sys
@ray.remote
def debug_env():
    print("Python executable:", sys.executable)
    import subprocess
    output = subprocess.check_output(["pip", "list"]).decode()
    print(output)



@ray.remote
def ray_process_data(input_path: str, output_path: str):
    logger.debug(f'Processing data in {input_path}')
    data_document = DataDocument(file_path=input_path)
    data_processor = CellTypeAnnotationDataProcessor()
    return data_processor.process_data(data_document=data_document, output_path=output_path)


class ProcessData(BaseTask):
    def __init__(self):
        super().__init__()

    def download_data_to_process(self) -> list[str]:
        return self.download_data(s3_input_folder=CHUNKED_DATA_PATH, local_output_folder=LOCAL_CHUNKED_DATA_PATH)


    def process_data(self, distributed: bool=False) -> list[str]:
        if distributed:
            logger.debug('Processsing data with Ray')
            return self.process_data_with_ray()
        else:
            logger.debug('Processsing data iteratively')
            return self.process_data_with_base_python()

    def process_data_with_base_python(self) -> list[str]:
        res = []
        data_processor = CellTypeAnnotationDataProcessor()
        for file_name in os.listdir(LOCAL_CHUNKED_DATA_PATH):
            local_file_path = os.path.join(LOCAL_CHUNKED_DATA_PATH, file_name)
            output_path = os.path.join(LOCAL_PROCESSED_DATA_PATH, f'{Path(file_name).stem}.dataset')
            logger.debug(f'Processing data in {local_file_path}')
            try:
                data_document = DataDocument(file_path=local_file_path)
                compressed_output_path = data_processor.process_data(data_document=data_document, output_path=output_path)
                shutil.rmtree(output_path)
                res.append(compressed_output_path)
            except Exception as e:
                s3_file_path = os.path.join(CHUNKED_DATA_PATH, file_name)
                s3_error_file_path = os.path.join(CHUNKED_DATA_ERROR_PATH, file_name)
                logger.error(f'Failed to process {local_file_path}, moving from {s3_file_path} to {s3_error_file_path} skipping due to {e}')
                self.s3_client.move_file(current_path=s3_file_path, new_path=s3_error_file_path)
                self.s3_client.unlock_file(locked_s3_path=s3_error_file_path)
            os.remove(local_file_path)
        return res


    # TODO
    def process_data_with_ray(self) -> list[str]:
        # this was define in the Dockerfile-ray-cpu
        ray.init(RAY_ENDPOINT, 
                     runtime_env={
                        "py_executable": "/app/.venv/bin/python",
                        "env_vars": {
                            "PATH": "/app/.venv/bin:$PATH",
                            "PYTHONPATH": "/app/src:$PYTHONPATH",
                        },
                    },
                )
        res = []
        to_delete = []
        to_process = []
        to_process.append(debug_env.remote())
        for file_name in os.listdir(LOCAL_CHUNKED_DATA_PATH):
            local_file_path = os.path.join(LOCAL_CHUNKED_DATA_PATH, file_name)
            output_path = os.path.join(LOCAL_PROCESSED_DATA_PATH, f'{Path(file_name).stem}.dataset')
            to_delete.append(local_file_path)
            # to_process.append(ray_process_data.remote(input_path=local_file_path,
            #                                           output_path=output_path))

        processed_data = ray.get(to_process)
        print('processed_data', processed_data)

            # try:
            #     file_chunks = SplitData.chunk_file(file_path=local_file_path)
            #     res.extend(file_chunks)
            # except Exception as e:
            #     s3_file_path = os.path.join(RAW_DATA_PATH, file_name)
            #     s3_error_file_path = os.path.join(RAW_DATA_ERROR_PATH, file_name)
            #     logger.error(f'Failed to chunk data in file {local_file_path}, moving from {s3_file_path} to {s3_error_file_path} skipping due to {e}')
            #     self.s3_client.move_file(current_path=s3_file_path, new_path=s3_error_file_path)
            #     self.s3_client.unlock_file(locked_s3_path=s3_error_file_path)
        for file_path in to_delete:
            os.remove(file_path)
        return res

    def delete_chunked_files(self, list_files: list[str]) -> list[str]:
        res = []
        for local_chunked_file_path in list_files:
            path_object = Path(local_chunked_file_path)
            file_name = path_object.name
            s3_chunked_file_path = os.path.join(CHUNKED_DATA_PATH, file_name)
            locked_s3_chunked_file_path = self.s3_client.get_locked_file_path(file_path=s3_chunked_file_path)
            if self.s3_client.delete_file(s3_path=locked_s3_chunked_file_path):
                res.append(locked_s3_chunked_file_path)
        return res

    def upload_processed_files(self, list_files: list[str]) -> list[str]:
        res = []
        for local_processed_file_path in list_files:
            path_object = Path(local_processed_file_path)
            file_name = path_object.name
            s3_chunk_file_path = os.path.join(PROCESSED_DATA_PATH, file_name)
            self.s3_client.upload_file(local_path=local_processed_file_path,
                                       s3_path=s3_chunk_file_path)
            os.remove(local_processed_file_path)
            res.append(local_processed_file_path)
        return res


if __name__ == '__main__':
    task = ProcessData()
    task.process_data_with_ray()