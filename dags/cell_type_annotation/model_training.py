
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from datetime import datetime, timedelta
import os
from airflow.sensors.python import PythonSensor
from airflow.models import Variable
CHECK_NEW_DATA_COUNT_TASK_ID = 'check_new_data_count'
TRAIN_TASK_ID = 'train'

# INSTALL_EXTRA_REQS_TASK_ID = 'install_extra_reqs'
PIP_LIST_TASK_ID = 'pip_list'
REMOVE_CACHE_TASK_ID = 'remove_cache'
CLEAN_XCOM_TASK_ID = 'clean_xcom'
START_TASK_ID = 'start'
END_TASK_ID = 'end'

KUBERNETES_NAMESPACE = Variable.get('KUBERNETES_NAMESPACE')
IMAGE_NAME = Variable.get('IMAGE_NAME')
print('here', KUBERNETES_NAMESPACE)


def has_counts(list_files: list[str]):
    if not list_files:
        return False
    return True


def check_for_new_annotated_data(**kwargs):
    from helical_pdqueiros.io.s3_client import ClientS3
    from helical_pdqueiros.io.logger import logger

    """Returns True if new annotated data is available in S3."""
    try:
        s3_client = ClientS3()
        new_annotated_data: list[str] = s3_client.get_new_annotated_data()
        return has_counts(new_annotated_data)
    except Exception as e:
        logger.error(f"Failed to connect to S3: {e}")
        return False

def to_train() -> str:
    '''checks new data folder and checks how much new annotated data there is,
    if there is enough, we train the model again, otherwise we let it be. This is basically to avoid retraining whenever data is stored'''
    try:
        s3_client = ClientS3()
        new_annotated_data: list[str] = s3_client.get_new_annotated_data()
    except Exception as e:
        logger.error(f'Failed to connect to S3 due to {e}')
    if has_counts():
        return TRAIN_TASK_ID
    else:
        return END_TASK_ID


def split_data():
    from helical_pdqueiros.jobs.cell_type_annotation.split_data import SplitDataJob
    job = SplitDataJob()
    job.run()
    # TODO add prometheus metrics push
    # job.publish_metrics()
 
def preprocess_data():
    
    # Clean and transform data
    import pandas as pd
    from sklearn.preprocessing import StandardScaler
     
    data = pd.read_parquet('/data/processed/raw_data.parquet')
    # Handle missing values
    data = data.dropna()
    # Feature engineering
    data['sales_per_day'] = data['total_sales'] / data['days_active']
    data.to_parquet('/data/processed/clean_data.parquet')
 
def train_model():
    # Train ML model
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    import joblib
     
    data = pd.read_parquet('/data/processed/clean_data.parquet')
    X = data.drop(['target'], axis=1)
    y = data['target']
     
    model = RandomForestRegressor(n_estimators=100)
    model.fit(X, y)
    joblib.dump(model, '/models/sales_model.pkl')
 

with DAG(
    dag_id="daily_wait_for_new_annotated_data",
    start_date=datetime(2025, 11, 1),
    schedule_interval="@daily",  # Run once per day
    catchup=False,  # Do not backfill past runs
) as dag:
    '''
    Workflow:
    - sensor to check for new data
    - if new data is detected:
        1. data X is downloaded
        2. data X is split and uploaded to s3 in batches X/batch_N.dataset
        3. each batch is processed
    '''
    wait_for_data = PythonSensor(
        task_id="wait_for_new_annotated_data",
        python_callable=check_for_new_annotated_data,
        poke_interval=60,
        timeout=600,
        # TODO check this
        mode="poke",
    )

    to_train_task = BranchPythonOperator(task_id=CHECK_NEW_DATA_COUNT_TASK_ID,
                                         python_callable=to_train)

    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=split_data,
        dag=dag
    )

    extract_task = KubernetesPodOperator(
        task_id="extract_data",
        namespace=KUBERNETES_NAMESPACE,
        image=IMAGE_NAME,
        cmds=["python", "-m", "extract"],
        name="extract-data-pod",
        get_logs=True,
        is_delete_operator_pod=True,
    )

    preprocess_task = PythonOperator(
        task_id='preprocess_data',
        python_callable=preprocess_data,
        dag=dag
    )

    train_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model,
        dag=dag
    )

    wait_for_data >> extract_task
    extract_task >> to_train_task
    to_train_task >> end
    to_train_task >> preprocess_task >> train_task
