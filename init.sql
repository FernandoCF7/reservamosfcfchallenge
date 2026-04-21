CREATE SCHEMA IF NOT EXISTS airflow;
CREATE SCHEMA IF NOT EXIStS django;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXIST raw.sales_raw (
    order_id TEXT
    , customer_id TEXT
    , product_id TEXT
    , region TEXT
    , order_date DATE
    , quantity INT
    , price NUMERIC
    , ingestion_ts tIMESTAMP DEFAULT CURRENT_TIMEStAMP
    , PRIMARY KEY (order_id)
);
