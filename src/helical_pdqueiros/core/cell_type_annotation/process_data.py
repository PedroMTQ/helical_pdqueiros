from helical_pdqueiros.io.logger import logger
from helical_pdqueiros.settings import RAW_DATA_PATH, BATCH_SIZE, LOCAL_RAW_DATA_PATH, LOCAL_CHUNKED_DATA_PATH, CHUNKED_DATA_PATH, RAW_DATA_ERROR_PATH, ARCHIVED_RAW_DATA_PATH
from helical_pdqueiros.core.documents.data_document import DataDocument
from helical_pdqueiros.core.base_task import BaseTask
import os
from pathlib import Path
from retry import retry

SLEEP_TIME = int(os.getenv('SLEEP_TIME', '0'))


class ProcessData(BaseTask):
    def __init__(self):
        super().__init__()

    def download_data_to_process(self) -> list[str]:
        return self.download_data(s3_input_folder=CHUNKED_DATA_PATH, local_output_folder=LOCAL_CHUNKED_DATA_PATH)

    def process_data(self) -> list[str]:
        res = []
        to_delete = []
        for file_name in os.listdir(LOCAL_RAW_DATA_PATH):
            local_file_path = os.path.join(LOCAL_RAW_DATA_PATH, file_name)
            logger.debug(f'Splitting data in {local_file_path}')
            to_delete.append(local_file_path)
            try:
                file_chunks = SplitData.chunk_file(file_path=local_file_path)
                res.extend(file_chunks)
            except Exception as e:
                s3_file_path = os.path.join(RAW_DATA_PATH, file_name)
                s3_error_file_path = os.path.join(RAW_DATA_ERROR_PATH, file_name)
                logger.error(f'Failed to chunk data in file {local_file_path}, moving from {s3_file_path} to {s3_error_file_path} skipping due to {e}')
                self.s3_client.move_file(current_path=s3_file_path, new_path=s3_error_file_path)
                self.s3_client.unlock_file(locked_s3_path=s3_error_file_path)
        for file_path in to_delete:
            os.remove(file_path)
        return res

    def upload_processed_files(self, list_files: list[str]) -> list[str]:
        res = []
        for local_chunk_file_path in list_files:
            path_object = Path(local_chunk_file_path)
            file_name = path_object.name
            s3_chunk_file_path = os.path.join(CHUNKED_DATA_PATH, file_name)
            self.s3_client.upload_file(local_path=local_chunk_file_path,
                                       s3_path=s3_chunk_file_path)
            os.remove(local_chunk_file_path)
            res.append(local_chunk_file_path)
        return res

    def archive_raw_data(self, list_files: list[str]) -> list[str]:
        res = []
        for file_path in list_files:
            file_name = Path(file_path).name
            s3_file_path = os.path.join(RAW_DATA_PATH, file_name)
            s3_locked_file_path = self.s3_client.get_locked_file_path(s3_file_path)
            archived_s3_file_path = os.path.join(ARCHIVED_RAW_DATA_PATH, file_name)
            self.s3_client.move_file(current_path=s3_locked_file_path, new_path=archived_s3_file_path)
            logger.info(f'Archived {s3_file_path} at {archived_s3_file_path}')
            res.append(archived_s3_file_path)
        return res


