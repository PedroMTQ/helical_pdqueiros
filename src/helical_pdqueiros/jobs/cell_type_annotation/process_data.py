import logging
from time import sleep

from helical_pdqueiros.core.cell_type_annotation.process_data import ProcessData
from helical_pdqueiros.jobs.base_job import BaseJob
from helical_pdqueiros.settings import SLEEP_TIME

logger = logging.getLogger(__name__)




class ProcessDataJob(BaseJob):
    '''
    sensor for download h5ad chunks (task), processing h5ad chunks (task), and uploading processed h5ad chunks to s3 (task)
    '''
    def __init__(self):
        self.task = ProcessData()

    def _run(self):
        # this could also be parallized if a client actually uploads new training data often enough, but I'd imagine that is not the case
        downloaded_files : list[str] = self.task.download_data_to_process()
        logger.info(f'Downloaded files: {downloaded_files}')
        if not downloaded_files:
            logger.info('Terminating job since no data was found...')
            return
        sleep(SLEEP_TIME)
        processed_files: list[str] = self.task.process_data()
        logger.info(f'Processed files: {processed_files}')
        sleep(SLEEP_TIME)
        deleted_files: list[str] = self.task.delete_chunked_files(list_files=downloaded_files)
        logger.info(f'Deleted files: {deleted_files}')
        sleep(SLEEP_TIME)
        uploaded_files: list[str] = self.task.upload_processed_files(list_files=processed_files)
        logger.info(f'Uploaded processed files: {uploaded_files}')



if __name__ == '__main__':
    job = ProcessDataJob()
    job.run()




