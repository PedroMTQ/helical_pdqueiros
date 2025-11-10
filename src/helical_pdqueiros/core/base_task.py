import logging
import os

from helical_pdqueiros.io.logger import setup_logger
from helical_pdqueiros.io.s3_client import ClientS3
from helical_pdqueiros.settings import H5AD_PATTERN

logger = logging.getLogger(__name__)
setup_logger(logger)


class BaseTask():
    def __init__(self):
        self.s3_client = ClientS3()

    def publish_metrics(self, ):
        pass

    def download_data(self, s3_input_folder, local_output_folder: str, limit: int=None, file_name_pattern: str=H5AD_PATTERN, lock_files: bool=True) -> list[str]:
        if lock_files:
            return self.download_data_with_lock(s3_input_folder=s3_input_folder, local_output_folder=local_output_folder, limit=limit, file_name_pattern=file_name_pattern)
        else:
            return self.download_data_without_lock(s3_input_folder=s3_input_folder, local_output_folder=local_output_folder, limit=limit, file_name_pattern=file_name_pattern)

    def download_data_without_lock(self, s3_input_folder, local_output_folder: str, limit: int=None, file_name_pattern: str=H5AD_PATTERN) -> list[str]:
        '''
        Downloads data from a given S3 folder into a local folder. A limit can be passed to allow for distributed work across multiple containers

        @param: s3_input_folder the S3 folder path
        @param: local_output_folder the local folder path
        @param: limit the number of files to download, defaults to None for no limit.
        '''
        res = []
        list_files: list[str] = self.s3_client.get_files(prefix=s3_input_folder, file_name_pattern=file_name_pattern)
        count = 0
        for s3_path in list_files:
            try:
                local_path = self.s3_client.download_file(s3_path=s3_path,
                                                                 output_folder=local_output_folder)
                res.append(local_path)
            except Exception as e:
                logger.error(f'Failed to download {s3_path} due to {e}')
            count += 1
            if limit:
                if count >= limit:
                    break
        return res

    def download_data_with_lock(self, s3_input_folder, local_output_folder: str, limit: int=None, file_name_pattern: str=H5AD_PATTERN) -> list[str]:
        '''
        Downloads data from a given S3 folder into a local folder. A limit can be passed to allow for distributed work across multiple containers

        @param: s3_input_folder the S3 folder path
        @param: local_output_folder the local folder path
        @param: limit the number of files to download, defaults to None for no limit.
        '''
        res = []
        list_files: list[str] = self.s3_client.get_files(prefix=s3_input_folder, file_name_pattern=file_name_pattern)
        count = 0
        for s3_path in list_files:
            # we lock the file to avoid other processes catching it again
            try:
                locked_s3_path = self.s3_client.lock_file(s3_path=s3_path)
            except Exception as e:
                logger.error(f'Failed to lock file, skipping {s3_path} due to {e}')
            try:
                locked_local_path = self.s3_client.download_file(s3_path=locked_s3_path,
                                                                 output_folder=local_output_folder)
                local_path = self.s3_client.get_unlocked_file_path(locked_local_path)
                os.rename(locked_local_path, local_path)
                res.append(local_path)
            except Exception as e:
                self.s3_client.unlock_file(locked_s3_path=s3_path)
                logger.error(f'Failed to download {s3_path} due to {e}')
            count += 1
            if limit:
                if count >= limit:
                    break
        return res

