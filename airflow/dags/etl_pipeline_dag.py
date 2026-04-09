import sys
sys.path.append("/opt/airflow/code")

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from etl.extract import extract
from etl.transform import transform
from etl.load import load_postgres

DATA_PATH = "/opt/airflow/code/source/events.json"
TMP_RAW = "/tmp/raw.parquet"
TMP_CLEAN = "/tmp/clean.parquet"

# --- wrappers for Airflow --- #

def extract_task():
    df = extract(DATA_PATH)
    df.to_parquet(TMP_RAW)

def transform_task():
    import pandas as pd
    df = pd.read_parquet(TMP_RAW)
    df_clean = transform(df)
    df_clean.to_parquet(TMP_CLEAN)

def load_task():
    import pandas as pd
    df = pd.read_parquet(TMP_CLEAN)
    load_postgres(df)

# --- DAG --- #

with DAG(
    dag_id="etl_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["challenge", "etl"]
) as dag:

    t1 = PythonOperator(
        task_id="extract",
        python_callable=extract_task
    )

    t2 = PythonOperator(
        task_id="transform",
        python_callable=transform_task
    )

    t3 = PythonOperator(
        task_id="load_postgres",
        python_callable=load_task
    )

    t1 >> t2 >> t3