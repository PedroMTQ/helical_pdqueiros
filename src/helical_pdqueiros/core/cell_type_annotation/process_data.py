import logging
import os
import shutil
from pathlib import Path

from helical_pdqueiros.core.base_task import BaseTask
from helical_pdqueiros.core.cell_type_annotation.data_processer import CellTypeAnnotationDataProcessor
from helical_pdqueiros.core.documents.data_document import DataDocument
from helical_pdqueiros.settings import (
    CHUNKED_DATA_ERROR_PATH,
    CHUNKED_DATA_PATH,
    LOCAL_CHUNKED_DATA_PATH,
    LOCAL_PROCESSED_DATA_PATH,
    PROCESSED_DATA_PATH,
    PROCESSING_CHUNKS_LIMIT,
)

logger = logging.getLogger(__name__)



class ProcessData(BaseTask):
    def __init__(self):
        super().__init__()

    def download_data_to_process(self) -> list[str]:
        return self.download_data(s3_input_folder=CHUNKED_DATA_PATH, local_output_folder=LOCAL_CHUNKED_DATA_PATH, limit=PROCESSING_CHUNKS_LIMIT or None)

    @staticmethod
    def compress_file(file_path: str) -> str:
        path_object = Path(file_path)
        compressed_file = shutil.make_archive(file_path, format='tar', root_dir=path_object.parent, base_dir=path_object.name)
        logger.debug(f"Compressed file_path to {compressed_file}")
        shutil.rmtree(file_path)
        return compressed_file


    def process_data(self) -> list[str]:
        res = []
        data_processor = CellTypeAnnotationDataProcessor()
        for file_name in os.listdir(LOCAL_CHUNKED_DATA_PATH):
            local_file_path = os.path.join(LOCAL_CHUNKED_DATA_PATH, file_name)
            output_path = os.path.join(LOCAL_PROCESSED_DATA_PATH, f'{Path(file_name).stem}.dataset')
            logger.debug(f'Processing data in {local_file_path}')
            try:
                data_document = DataDocument(file_path=local_file_path)
                output_path = data_processor.process_data(data_document=data_document, output_path=output_path)
                compressed_output_path = ProcessData.compress_file(file_path=output_path)
                res.append(compressed_output_path)
            except Exception as e:
                s3_file_path = os.path.join(CHUNKED_DATA_PATH, file_name)
                s3_error_file_path = os.path.join(CHUNKED_DATA_ERROR_PATH, file_name)
                logger.error(f'Failed to process {local_file_path}, moving from {s3_file_path} to {s3_error_file_path} skipping due to {e}')
                self.s3_client.move_file(current_path=s3_file_path, new_path=s3_error_file_path)
                self.s3_client.unlock_file(locked_s3_path=s3_error_file_path)
        os.remove(local_file_path)
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
