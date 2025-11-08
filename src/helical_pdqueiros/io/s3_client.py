import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import boto3

from helical_pdqueiros.io.logger import logger
from helical_pdqueiros.settings import (
    S3_ACCESS_KEY,
    S3_SECRET_ACCESS_KEY,
    MINIO_HOST,
    MINIO_PORT,
    RAW_DATA_PATH,
    DATA,
    CHUNKED_DATA_PATH,
    TRAINING_DATA_PATH,
    PROCESSED_DATA_PATH,
    LOCAL_RAW_DATA_PATH,
    LOCAL_CHUNKED_DATA_PATH,
    H5AD_PATTERN,
    HELICAL_S3_BUCKET,
)





class ClientS3():
    lock_string = '.lock'
    def __init__(self,
                 aws_access_key_id: str=S3_ACCESS_KEY,
                 aws_secret_access_key: str=S3_SECRET_ACCESS_KEY,
                 s3_host: str=MINIO_HOST,
                 s3_port: str=MINIO_PORT,
                 # Im assuming we only use one bucket
                 bucket_name: str=HELICAL_S3_BUCKET):
        self.__s3_access_key_id = aws_access_key_id
        self.__s3_secret_access_key = aws_secret_access_key
        self.__s3_host = s3_host
        self.__s3_port = s3_port
        self.__bucket_name = bucket_name
        self.__client = boto3.client('s3',
                                     aws_access_key_id=self.__s3_access_key_id,
                                     aws_secret_access_key=self.__s3_secret_access_key,
                                     endpoint_url=f'http://{self.__s3_host}:{self.__s3_port}',
                                    )
        self.test_s3_connection()

    def test_s3_connection(self):
        try:
            self.__client.head_bucket(Bucket=self.__bucket_name)
            logger.debug(f"Connected to S3 bucket: {self.__bucket_name}")
            return True
        except Exception as e:
            raise Exception(f"Error accessing bucket {self.__bucket_name} due to: {e}") from e

    def get_files(self, prefix: str, file_name_pattern: str, match_on_s3_path: bool=False) -> list[str]:
        res = []
        try:
            response = self.__client.list_objects_v2(Bucket=HELICAL_S3_BUCKET, Prefix=prefix)
        except Exception as e:
            raise e
        regex_pattern = re.compile(file_name_pattern)
        for obj in response.get("Contents", []):
            s3_path = obj["Key"]
            file_name = Path(s3_path).name
            if regex_pattern.fullmatch(file_name) or (match_on_s3_path and regex_pattern.fullmatch(s3_path)):
                res.append(s3_path)
            else:
                logger.debug(f'File skipped: {s3_path}')
        return res

    def get_raw_data(self) -> list[str]:
        files = self.get_files(prefix=RAW_DATA_PATH, file_name_pattern=H5AD_PATTERN)
        logger.debug(f'Raw data: {files}')
        return files

    def get_processsed_data(self) -> list[str]:
        return self.get_files(prefix=ANNOTATED_DATA_PATH, file_name_pattern=H5AD_PATTERN)

    @staticmethod
    def get_locked_file_path(file_path):
        return f'{file_path}{ClientS3.lock_string}'

    @staticmethod
    def get_unlocked_file_path(file_path):
        return file_path.removesuffix(ClientS3.lock_string)

    def lock_file(self, s3_path: str) -> str:
        locked_s3_path = ClientS3.get_locked_file_path(s3_path)
        self.__client.copy_object(Bucket=self.__bucket_name, CopySource={'Bucket': self.__bucket_name, 'Key': s3_path}, Key=locked_s3_path)
        self.move_file(current_path=s3_path, new_path=locked_s3_path)
        return locked_s3_path

    def unlock_file(self, locked_s3_path: str) -> str:
        s3_path = ClientS3.get_unlocked_file_path(locked_s3_path)
        self.move_file(current_path=locked_s3_path, new_path=s3_path)
        return s3_path

    def move_file(self, current_path: str, new_path: str) -> str:
        try:
            self.__client.copy_object(Bucket=self.__bucket_name, CopySource={'Bucket': self.__bucket_name, 'Key': current_path}, Key=new_path)
            self.__client.delete_object(Bucket=self.__bucket_name, Key=current_path)
        except Exception as e:
            logger.exception(f'Failed to move {current_path} to {new_path} due to {e}')
        return new_path

    def download_file(self, s3_path: str, output_folder: str) -> str:
        '''
        returns path of the downloaded file
        '''
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        file_name = Path(s3_path).name
        local_path = os.path.join(output_folder, file_name)
        self.__client.download_file(self.__bucket_name, s3_path, local_path)
        logger.debug(f'Downloaded {s3_path} to {output_folder}')
        return local_path

    def upload_file(self, local_path: str, s3_path: str) -> None:
        '''
        Uploads a local file to S3 at the given s3_path.
        '''
        self.__client.upload_file(Filename=local_path, Bucket=self.__bucket_name, Key=s3_path)

    def file_exists(self, s3_path: str) -> bool:
        try:
            self.__client.get_object(Bucket=self.__bucket_name, Key=s3_path)
            return True
        except Exception as _:
            return False


if __name__ == '__main__':
    client = ClientS3()
    # print(client.file_exists('boxes/output/bounding_box_01976a1225ca7e32a2daad543cb4391e.jsonl'))
    # print(client.get_files(FIELDS_FOLDER_OUTPUT, file_name_pattern='fields/input/01976dbcbdb77dc4b9b61ba545503b77/fields_2025-06-04-BATCH_2.jsonl', match_on_s3_path=True))

    print(client.get_input_fields())
