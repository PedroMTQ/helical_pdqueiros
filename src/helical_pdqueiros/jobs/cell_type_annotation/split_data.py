from helical_pdqueiros.io.logger import logger
from helical_pdqueiros.settings import RAW_DATA_PATH, BATCH_SIZE, LOCAL_RAW_DATA_PATH, LOCAL_CHUNKED_DATA_PATH, DATA, CHUNKED_DATA_PATH, RAW_DATA_ERROR_PATH, ARCHIVE_RAW_DATA_PATH
from helical_pdqueiros.core.documents.data_document import DataDocument
from helical_pdqueiros.jobs.base_job import BaseJob
import os
from pathlib import Path
import anndata as ad


class SplitDataJob(BaseJob):
    '''
    job for:
    downloading all data from S3 new_data to local data folder
    splits all data into batches
    uploads all batches to S3
    moves processed data to old_data
    '''
    def __init__(self):
        super().__init__()

    def download_data(self) -> list[str]:
        res = []
        list_files: list[str] = self.s3_client.get_raw_data()
        for s3_path in list_files:
            # we lock the file to avoid other processes catching it again
            try:
                locked_s3_path = self.s3_client.lock_file(s3_path=s3_path)
            except Exception as e:
                logger.error(f'Failed to lock file, skipping {s3_path} due to {e}')
            try:
                locked_local_path = self.s3_client.download_file(s3_path=locked_s3_path,
                                                                 output_folder=LOCAL_RAW_DATA_PATH)
                local_path = locked_local_path.removesuffix(self.s3_client.lock_string)
                os.rename(locked_local_path, local_path)
                res.append(local_path)
            except Exception as e:
                self.s3_client.unlock_file(locked_s3_path=s3_path)
                logger.error(f'Failed to download raw data: {s3_path} due to {e}')
        return res

    def split_data(self) -> list[str]:
        res = []
        to_delete = []
        for file_name in os.listdir(LOCAL_RAW_DATA_PATH):
            local_file_path = os.path.join(LOCAL_RAW_DATA_PATH, file_name)
            logger.debug(f'Splitting data in {local_file_path}')
            to_delete.append(local_file_path)
            try:
                data_document = DataDocument(file_path=local_file_path)
                chunk: DataDocument
                for chunk in data_document.yield_chunks(chunk_size=BATCH_SIZE):
                    local_chunk_file_path = chunk.save(output_folder=LOCAL_CHUNKED_DATA_PATH)
                    res.append(local_chunk_file_path)
            except Exception as e:
                s3_file_path = os.path.join(RAW_DATA_PATH, file_name)
                s3_error_file_path = os.path.join(RAW_DATA_ERROR_PATH, file_name)
                logger.error(f'Failed to chunk data in file {local_file_path}, moving from {s3_file_path} to {s3_error_file_path} skipping due to {e}')
                self.s3_client.move_file(current_path=s3_file_path, new_path=s3_error_file_path)
                self.s3_client.unlock_file(locked_s3_path=s3_error_file_path)
        for file_path in to_delete:
            os.remove(file_path)
        return res

    def upload_chunked_files(self, list_files: list[str]):
        for local_chunk_file_path in list_files:
            path_object = Path(local_chunk_file_path)
            file_name = path_object.name
            s3_chunk_file_path = os.path.join(CHUNKED_DATA_PATH, file_name)
            self.s3_client.upload_file(local_path=local_chunk_file_path,
                                       s3_path=s3_chunk_file_path)

    def archive_raw_data(self, list_files: list[str]) -> list[str]:
        res = []
        for file_path in list_files:
            file_name = Path(file_path).name
            s3_file_path = os.path.join(RAW_DATA_PATH, file_name)
            s3_locked_file_path = self.s3_client.get_locked_file_path(s3_file_path)
            archived_s3_file_path = os.path.join(ARCHIVE_RAW_DATA_PATH, file_name)
            self.s3_client.move_file(current_path=s3_locked_file_path, new_path=archived_s3_file_path)
            logger.info(f'Archived {s3_file_path} at {archived_s3_file_path}')
            res.append(archived_s3_file_path)
        return res

    def run(self):
        # this could also be parallized if a client actually uploads new training data often enough, but I'd image that is not the case
        downloaded_files : list[str] = self.download_data()
        logger.info(f'Downloaded files: {downloaded_files}')
        chunked_files: list[str] = self.split_data()
        logger.info(f'Chunked files: {chunked_files}')
        uploaded_files = self.upload_chunked_files(list_files=chunked_files)
        logger.info(f'Uploaded files: {uploaded_files}')
        archived_files = self.archive_raw_data(list_files=downloaded_files)
        logger.info(f'Archived files: {archived_files}')


if __name__ == '__main__':
    job = SplitDataJob()
    job.run()




