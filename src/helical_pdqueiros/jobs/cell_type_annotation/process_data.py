from helical_pdqueiros.core.cell_type_annotation.process_data import ProcessData
import os
from time import sleep
import logging
from helical_pdqueiros.io.logger import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

SLEEP_TIME = int(os.getenv('SLEEP_TIME', '0'))



class ProcessDataJob():
    '''
    sensor for download h5ad chunks (task), processing h5ad chunks (task), and uploading processed h5ad chunks to s3 (task)
    '''
    def run(self):
        '''
        Wrapper for dev testing, which would be replaced by Airflow
        '''
        print('here')
        task = ProcessData()
        # this could also be parallized if a client actually uploads new training data often enough, but I'd imagine that is not the case
        downloaded_files : list[str] = task.download_data_to_process()
        logger.info(f'Downloaded files: {downloaded_files}')
        if not downloaded_files:
            logger.info('Terminating job since no data was found...')
            return
        sleep(SLEEP_TIME)
        processed_files: list[str] = task.process_data()
        logger.info(f'Processed files: {processed_files}')
        sleep(SLEEP_TIME)
        deleted_files: list[str] = task.delete_chunked_files(list_files=downloaded_files)
        logger.info(f'Deleted files: {deleted_files}')
        sleep(SLEEP_TIME)
        uploaded_files = task.upload_processed_files(list_files=processed_files)
        logger.info(f'Uploaded processed files: {uploaded_files}')



if __name__ == '__main__':
    job = ProcessDataJob()
    job.run()




