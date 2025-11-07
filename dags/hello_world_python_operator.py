from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def hello_world():
    from time import sleep
    logger.info('Hello World, I am about to sleep!')
    sleep(60)
    logger.info('I woke up after 60 seconds!')


with DAG('dag.hello_world_and_sleep_python_operator', default_args=default_args, schedule='1 * * * *') as dag:
    hello_world_task = PythonOperator(
        task_id="task.hello_world_and_sleep_python_operator",
        python_callable=hello_world,
    )
