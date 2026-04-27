import sys
sys.path.append("/opt/airflow/code")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime

from etl.raw import (
    load_raw_sales
    , load_raw_customers
    , load_raw_products
)

from etl.staging import (
    transform_sales_to_stg
    , transform_customers_to_stg
    , transform_products_to_stg
)

from etl.dimension import (
    load_dim_customers_scd2
    , load_dim_products_scd2
    , load_fact_sales
)

with DAG(
    dag_id="etl_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["etl", "celery", "parallel"]
) as dag:

    # -------------------------
    # RAW
    # -------------------------

    sales_files = [
        ("ventas_norte.json", "norte")
        , ("ventas_centro.json", "centro")
        , ("ventas_occidente.json", "occidente")
        , ("ventas_sur.json", "sur")
    ]

    raw_sales_tasks = []

    for file_name, label in sales_files:

        t = PythonOperator(
            task_id=f"load_raw_sales_{label}",
            python_callable=load_raw_sales,
            op_args=[f"/opt/airflow/code/source/{file_name}", label]
        )
        raw_sales_tasks.append(t)
    
    customer_files = [
        ("clientes_norte.json", "norte")
        , ("clientes_centro.json", "centro")
        , ("clientes_occidente.json", "occidente")
        , ("clientes_sur.json", "sur"),
    ]

    raw_customer_tasks = []

    for file_name, label in customer_files:
        t = PythonOperator(
            task_id=f"load_raw_customers_{label}",
            python_callable=load_raw_customers,
            op_args=[f"/opt/airflow/code/source/{file_name}", label]
        )
        raw_customer_tasks.append(t)
    
    raw_products_task = PythonOperator(
        task_id="load_raw_products",
        python_callable=load_raw_products,
        op_args=["/opt/airflow/code/source/productos.json", "productos"]
    )



    # -------------------------
    # STAGING
    # -------------------------
    
    stg_sales = PythonOperator(
        task_id="stg_sales",
        python_callable=transform_sales_to_stg
    )
    
    stg_customers = PythonOperator(
        task_id="stg_customers",
        python_callable=transform_customers_to_stg
    )
    
    stg_products = PythonOperator(
        task_id="stg_products",
        python_callable=transform_products_to_stg
    )

    # -------------------------
    # DIMENTION
    # -------------------------

    dim_customers_task = PythonOperator(
        task_id="dim_customers_scd2",
        python_callable=load_dim_customers_scd2
    )

    dim_products_task = PythonOperator(
        task_id="dim_products_scd2",
        python_callable=load_dim_products_scd2
    )

    # -------------------------
    # FACT
    # -------------------------

    fact_sales_task = PythonOperator(
        task_id="fact_sales",
        python_callable=load_fact_sales
    )
    

    # -------------------------
    # DEPENDENCE
    # -------------------------

    # RAW → STAGING
    raw_sales_tasks >> stg_sales
    raw_customer_tasks >> stg_customers
    raw_products_task >> stg_products

    # STAGING → DIM
    stg_customers >> dim_customers_task
    stg_products >> dim_products_task

    # ALL --> FACT
    [stg_sales, dim_customers_task, dim_products_task] >> fact_sales_task