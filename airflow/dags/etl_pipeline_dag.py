import sys
sys.path.append("/opt/airflow/code")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime

from etl.extract import extract
from etl.transform import transform
from etl.load import load_postgres

import pandas as pd

# --- wrappers for Airflow --- #

def extract_task(path, tmp_raw):
    df = extract(path)
    df.to_parquet(tmp_raw)

def transform_task(tmp_raw, tmp_clean):
    import pandas as pd
    df = pd.read_parquet(tmp_raw)
    df_clean = transform(df)
    df_clean.to_parquet(tmp_clean)

def load_task(tmp_clean):
    import pandas as pd
    df = pd.read_parquet(tmp_clean)
    load_postgres(df)

# --- DAG --- #

def build_process(group_id):
    
    idx_files = ["1", "2", "3", "4"]

    with TaskGroup(group_id=group_id) as tg:

        for suffix in idx_files:

            DATA_PATH = f"/opt/airflow/code/source/events_{suffix}.json"
            TMP_RAW = f"/shared_tmp/raw_{group_id}_{suffix}.parquet"
            TMP_CLEAN = f"/shared_tmp/clean_{group_id}_{suffix}.parquet"

            extract_t = PythonOperator(
                task_id=f"extract_{suffix}",
                python_callable=extract_task,
                op_args=[DATA_PATH, TMP_RAW]
            )

            transform_t = PythonOperator(
                task_id=f"transform_{suffix}",
                python_callable=transform_task,
                op_args=[TMP_RAW, TMP_CLEAN]
            )

            load_t = PythonOperator(
                task_id=f"load_{suffix}",
                python_callable=load_task,
                op_args=[TMP_CLEAN]
            )

            extract_t >> transform_t >> load_t

    return tg

with DAG(
    dag_id="etl_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["etl", "celery", "parallel"]
) as dag:

    process_A = build_process("proceso_A")
    process_B = build_process("proceso_B")
    process_C = build_process("proceso_C")
    process_D = build_process("proceso_D")

    # dependences
    process_A >> process_B