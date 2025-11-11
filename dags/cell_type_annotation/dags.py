import logging
import os
from typing import Literal

import pendulum
from airflow.models.dag import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount, DeviceRequest
from dotenv import dotenv_values

IMAGE_NAME = 'helical-pdqueiros:latest'
CONTAINER_DATA_PATH = '/app/tmp'
LOCAL_DATA_PATH = '/home/pedroq/workspace/helical_pdqueiros/tmp'
ENV_FILE = '/app/.env'
logger = logging.getLogger(__name__)
EXPERIMENT_NAME = os.getenv('EXPERIMENT_NAME', 'cell_type_classification')
CUDA_DEVICE_ID = os.getenv('CUDA_DEVICE_ID', '')


def get_task(execution_type: Literal['split_data', 'process_data', 'fine_tune'], device_requests: list=None, container_suffix: str=''):
    command_to_run = f'helical_pdqueiros {execution_type}'
    # https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/_api/airflow/providers/docker/operators/docker/index.html
    return DockerOperator(
            task_id=f"run_helical_pdqueiros.{execution_type}",
            container_name=f'helical-pdqueiros.{execution_type}{container_suffix}',
            image=IMAGE_NAME,
            mounts=[
                # https://docker-py.readthedocs.io/en/stable/api.html?highlight=mount#docker.types.Mount
                Mount(source=LOCAL_DATA_PATH, target=CONTAINER_DATA_PATH, type='bind', read_only=False)
                    ],
            command=command_to_run,
            private_environment  = dotenv_values(ENV_FILE),
            api_version='1.51',
            # api_version='auto',
            network_mode="helical-network",
            auto_remove='force',
            # for docker in docker (tecnativa/docker-socket-proxy:v0.4.1) -> https://github.com/benjcabalona1029/DockerOperator-Airflow-Container/tree/master
            mount_tmp_dir=False,
            docker_url="tcp://airflow-docker-socket:2375",
            device_requests=device_requests,
        )

with DAG(
    dag_id=f'{EXPERIMENT_NAME}.data_processing',
    start_date=pendulum.datetime(2025, 1, 1),
    # schedule='0 * * * *',
    catchup=False,
    tags=["helical-pdqueiros", 'data_processing'],
    ) as dag:
        split_data_task = get_task(execution_type='split_data')
        process_data_task = get_task(execution_type='process_data')
        split_data_task >> process_data_task

with DAG(
    dag_id=f'{EXPERIMENT_NAME}.model_fine_tuning',
    start_date=pendulum.datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["helical-pdqueiros", 'fine_tuning'],
    ) as dag:
        fine_tune_task = get_task(execution_type='fine_tune',
                                  container_suffix='-gpu',
                                  device_requests=DeviceRequest(device_ids=[CUDA_DEVICE_ID.split(',')], capabilities=[['gpu']]) if CUDA_DEVICE_ID else None)

