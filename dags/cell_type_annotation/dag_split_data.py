import logging
from dotenv import dotenv_values
import pendulum
from airflow.models.dag import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount


IMAGE_NAME = 'helical-pdqueiros:latest'
EXECUTION_TYPE = 'split_data'
CONTAINER_DATA_PATH = '/app/tmp'
LOCAL_DATA_PATH = '/home/pedroq/workspace/helical_pdqueiros/tmp'
ENV_FILE = '/app/.env'
COMMAND_TO_RUN = f'helical_pdqueiros {EXECUTION_TYPE}'
logger = logging.getLogger(__name__)

with DAG(
    dag_id=EXECUTION_TYPE,
    start_date=pendulum.datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["helical-pdqueiros", EXECUTION_TYPE],
) as dag:

    # https://airflow.apache.org/docs/apache-airflow-providers-docker/stable/_api/airflow/providers/docker/operators/docker/index.html
    operator_task = DockerOperator(
        task_id=f"run_helical_pdqueiros.{EXECUTION_TYPE}",
        container_name=f'helical-pdqueiros.{EXECUTION_TYPE}',
        image=IMAGE_NAME,
        mounts=[
            # https://docker-py.readthedocs.io/en/stable/api.html?highlight=mount#docker.types.Mount
            Mount(source=LOCAL_DATA_PATH, target=CONTAINER_DATA_PATH, type='bind', read_only=False)
                ],
        command=COMMAND_TO_RUN,
        private_environment  = dotenv_values(ENV_FILE),
        api_version='1.51',
        network_mode="helical-network",
        auto_remove='force',
        # for docker in docker (tecnativa/docker-socket-proxy:v0.4.1) -> https://github.com/benjcabalona1029/DockerOperator-Airflow-Container/tree/master
        mount_tmp_dir=False,
        docker_url="TCP://airflow-docker-socket:2375",
    )
