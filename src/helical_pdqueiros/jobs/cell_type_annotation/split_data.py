from helical_pdqueiros.io.s3_client import ClientS3
from helical_pdqueiros.io.logger import logger
from helical_pdqueiros.settings import RAW_DATA_PATH, BATCH_SIZE, CHUNKED_DATA_PATH
from helical_pdqueiros.core.documents.data_document import DataDocument
import os
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
        self.s3_client = ClientS3()

    def __download_data(self) -> list[str]:
        res = []
        list_files: list[str] = self.s3_client.get_new_annotated_data()
        for s3_path in list_files:
            try:
                self.s3_client.download_file(s3_path=s3_path,
                                            output_folder=RAW_DATA_PATH)
                res.append(s3_path)
            except Exception as e:
                logger.error(f'Failed to download raw data: {s3_path}')
        return res

    def __split_data(self) -> list[str]:
        res = []
        for file_name in os.listdir(RAW_DATA_PATH):
            file_path = os.path.join(RAW_DATA_PATH, file_name)
            data_document = DataDocument(data=ad.read_h5ad(file_path))
            chunk: DataDocument
            for chunk in data_document.yield_chunks(BATCH_SIZE):
                chunk.save()
                res.append(chunk.file_path)
        return res

    def __upload_files(self, list_files: list[str]):
        for file_path in list_files:
            self.s3_client.upload_file(local_path=file_path,
                                       s3_path=s3_path)

    def run(self):
        # this could also be parallized if a client actually uploads new training data often enough, but I'd image that is not the case
        downloaded_files : list[str] = self.__download_data()
        chunked_files: list[str] = self.__split_data()
        self.__upload_files(list_files=chunked_files)


