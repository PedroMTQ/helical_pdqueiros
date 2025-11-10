import logging
from dotenv import dotenv_values
import pendulum
from typing import Literal
from airflow.models.dag import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount
import os

IMAGE_NAME = 'helical-pdqueiros:latest'
CONTAINER_DATA_PATH = '/app/tmp'
LOCAL_DATA_PATH = '/home/pedroq/workspace/helical_pdqueiros/tmp'
ENV_FILE = '/app/.env'
logger = logging.getLogger(__name__)
EXPERIMENT_NAME = os.getenv('EXPERIMENT_NAME', 'cell_type_classification')


def create_dag(execution_type: Literal['split_data', 'process_data', 'fine_tune'], schedule: str=None):
    command_to_run = f'helical_pdqueiros {execution_type}'
    with DAG(
        dag_id=f'{EXPERIMENT_NAME}.{execution_type}',
        start_date=pendulum.datetime(2025, 1, 1),
        schedule=schedule,
        catchup=False,
        tags=["helical-pdqueiros", execution_type],
    ) as dag:
        # https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/_api/airflow/providers/docker/operators/docker/index.html
        operator_task = DockerOperator(
            task_id=f"run_helical_pdqueiros.{execution_type}",
            container_name=f'helical-pdqueiros.{execution_type}',
            image=IMAGE_NAME,
            mounts=[
                # https://docker-py.readthedocs.io/en/stable/api.html?highlight=mount#docker.types.Mount
                Mount(source=LOCAL_DATA_PATH, target=CONTAINER_DATA_PATH, type='bind', read_only=False)
                    ],
            command=command_to_run,
            private_environment  = dotenv_values(ENV_FILE),
            api_version='1.51',
            network_mode="helical-network",
            auto_remove='force',
            # for docker in docker (tecnativa/docker-socket-proxy:v0.4.1) -> https://github.com/benjcabalona1029/DockerOperator-Airflow-Container/tree/master
            mount_tmp_dir=False,
            docker_url="TCP://airflow-docker-socket:2375",
        )
    return dag


dag = create_dag(execution_type='split_data')
dag = create_dag(execution_type='process_data')
dag = create_dag(execution_type='fine_tune')