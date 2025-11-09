from helical_pdqueiros.io.s3_client import ClientS3
from helical_pdqueiros.settings import (
    H5AD_PATTERN)

import os
import logging
from helical_pdqueiros.io.logger import setup_logger


logger = logging.getLogger(__name__)
setup_logger(logger)


class BaseTask():
    def __init__(self):
        self.s3_client = ClientS3()

    def publish_metrics(self, ):
        pass

    def download_data(self, s3_input_folder, local_output_folder: str) -> list[str]:
        res = []
        list_files: list[str] = self.s3_client.get_files(prefix=s3_input_folder, file_name_pattern=H5AD_PATTERN)
        for s3_path in list_files:
            # we lock the file to avoid other processes catching it again
            try:
                locked_s3_path = self.s3_client.lock_file(s3_path=s3_path)
            except Exception as e:
                logger.error(f'Failed to lock file, skipping {s3_path} due to {e}')
            try:
                locked_local_path = self.s3_client.download_file(s3_path=locked_s3_path,
                                                                 output_folder=local_output_folder)
                local_path = locked_local_path.removesuffix(self.s3_client.lock_string)
                os.rename(locked_local_path, local_path)
                res.append(local_path)
            except Exception as e:
                self.s3_client.unlock_file(locked_s3_path=s3_path)
                logger.error(f'Failed to download {s3_path} due to {e}')
        return res
