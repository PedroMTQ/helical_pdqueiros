from helical_pdqueiros.io.logger import logger
from helical_pdqueiros.core.cell_type_annotation.split_data import SplitData
import os


SLEEP_TIME = int(os.getenv('SLEEP_TIME', '0'))
from time import sleep



class SplitDataJob():
    '''
    sensor for downloading h5ad (task), splitting data into chunks (task) and uploading unprocessed h5ad chunks to S3 (task)
    '''

    def run(self):
        '''
        Wrapper for dev testing, which would be replaced by Airflow
        '''
        task = SplitData()
        # this could also be parallized if a client actually uploads new training data often enough, but I'd imagine that is not the case
        downloaded_files : list[str] = task.download_data_to_split()
        logger.info(f'Downloaded files: {downloaded_files}')
        if not downloaded_files:
            logger.info('Terminating job since no data was found...')
            return
        sleep(SLEEP_TIME)
        chunked_files: list[str] = task.split_data()
        logger.info(f'Chunked files: {chunked_files}')
        sleep(SLEEP_TIME)
        uploaded_files = task.upload_chunked_files(list_files=chunked_files)
        logger.info(f'Uploaded chunk files: {uploaded_files}')
        sleep(SLEEP_TIME)
        archived_files = task.archive_raw_data(list_files=downloaded_files)
        logger.info(f'Archived files: {archived_files}')



if __name__ == '__main__':
    job = SplitDataJob()
    job.run()




