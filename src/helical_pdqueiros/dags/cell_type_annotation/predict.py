

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta


def extract_data():
    # Extract data from source
    import pandas as pd
    data = pd.read_csv('/data/raw/sales_data.csv')
    data.to_parquet('/data/processed/raw_data.parquet')
 
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
 
def predict():
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
 
# Define DAG
dag = DAG(
    'ml_pipeline',
    default_args={
        'owner': 'data-team',
        'depends_on_past': False,
        'start_date': datetime(2024, 1, 1),
        'retries': 2,
        'retry_delay': timedelta(minutes=5)
    },
    schedule_interval='@daily',
    catchup=False
)
 
# Define tasks
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag
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
 
# Set dependencies
extract_task >> preprocess_task >> train_task