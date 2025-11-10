import logging
import os
from time import sleep

from helical_pdqueiros.core.cell_type_annotation.fine_tune import FineTune
from helical_pdqueiros.io.logger import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

SLEEP_TIME = int(os.getenv('SLEEP_TIME', '0'))


class FineTuneJob():
    '''
        reads processed h5ad chunks (i.e., *.dataset) from new and archived processed data.  Trains model from streamed chunks, and logs it into Mlflow
    '''


    def run(self):
        task = FineTune()
        downloaded_files : list[str] = task.download_data_to_fine_tune()
        logger.info(f'Downloaded files: {downloaded_files}')
        if not downloaded_files:
            logger.info('Terminating job since no data was found...')
            return
        sleep(SLEEP_TIME)
        uncompressed_files: list[str] = task.uncompress_data(list_files=downloaded_files)
        logger.info(f'Uncompressed training files: {uncompressed_files}')
        sleep(SLEEP_TIME)
        fine_tuning_files: list[str] = task.fine_tune(list_files=uncompressed_files)
        logger.info(f'Fine-tuned with: {fine_tuning_files}')
        sleep(SLEEP_TIME)
        archived_files: list[str] = task.archive_processed_data()
        logger.info(f'Archived training files: {archived_files}')
        sleep(SLEEP_TIME)


if __name__ == '__main__':
    job = FineTuneJob()
    job.run()




