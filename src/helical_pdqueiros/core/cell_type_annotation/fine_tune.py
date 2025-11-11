import logging
import os
import shutil
from pathlib import Path
from helical_pdqueiros.core.base_task import BaseTask
from helical_pdqueiros.core.cell_type_annotation.fine_tuner import CellTypeAnnotationFineTuner
from helical_pdqueiros.io.logger import setup_logger
from helical_pdqueiros.settings import (
    ARCHIVED_PROCESSED_DATA_PATH,
    DATASET_PATTERN,
    LOCAL_PROCESSED_DATA_PATH,
    PROCESSED_DATA_PATH,
)

logger = logging.getLogger(__name__)
setup_logger(logger)

SLEEP_TIME = int(os.getenv('SLEEP_TIME', '0'))
RAY_ENDPOINT = os.getenv('RAY_ENDPOINT', 'ray://localhost:10001')



class FineTune(BaseTask):
    '''Fine tunes model given a list of processed data chunks. Needs to be manually triggered'''
    def __init__(self):
        super().__init__()
        self.__new_processed_data: list[str] = []

    def download_data_to_fine_tune(self) -> list[str]:
        res = self.download_data(s3_input_folder=PROCESSED_DATA_PATH, local_output_folder=LOCAL_PROCESSED_DATA_PATH, file_name_pattern=DATASET_PATTERN, lock_files=False)
        self.__new_processed_data: list[str] = list(res)
        logger.debug(f'New data for fine-tuning: {res}')
        # I'm assuming we always start from the same base model, if not, we could instead just download the modell from mlflow
        old_processed_data = self.download_data(s3_input_folder=ARCHIVED_PROCESSED_DATA_PATH, local_output_folder=LOCAL_PROCESSED_DATA_PATH, file_name_pattern=DATASET_PATTERN, lock_files=False)
        logger.debug(f'Archived data for fine-tuning: {old_processed_data}')
        res.extend(old_processed_data)
        return res

    def uncompress_data(self, list_files: list[str]) -> list[str]:
        res = []
        for file_path in list_files:
            uncompressed_file_path = os.path.join(LOCAL_PROCESSED_DATA_PATH, Path(file_path).stem)
            shutil.unpack_archive(filename=file_path, extract_dir=LOCAL_PROCESSED_DATA_PATH)
            res.append(uncompressed_file_path)
        return res

    def fine_tune(self, list_files: list[str]) -> bool:
        fine_tuner = CellTypeAnnotationFineTuner()
        fine_tuner.run(chunk_paths=list_files)
        return list_files

    def archive_processed_data(self) -> list[str]:
        res = []
        for file_path in self.__new_processed_data:
            file_name = Path(file_path).name
            s3_file_path = os.path.join(PROCESSED_DATA_PATH, file_name)
            archived_s3_file_path = os.path.join(ARCHIVED_PROCESSED_DATA_PATH, file_name)
            self.s3_client.move_file(current_path=s3_file_path, new_path=archived_s3_file_path)
            logger.debug(f'Archived {s3_file_path} at {archived_s3_file_path}')
            res.append(archived_s3_file_path)
        return res


    def delete_local_processed_files(self, list_files: list[str]) -> list[str]:
        for file_path in list_files:
            os.remove(file_path)
        return list_files


if __name__ == '__main__':
    task = FineTune()
    task.download_data_to_fine_tune()
