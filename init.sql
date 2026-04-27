CREATE SCHEMA IF NOT EXISTS airflow;
CREATE SCHEMA IF NOT EXIStS django;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

--- raw ---

CREATE TABLE IF NOT EXISTS raw.sales_raw (
    order_id TEXT
    , customer_id TEXT
    , product_id TEXT
    , region TEXT
    , order_date DATE
    , quantity INT
    , price NUMERIC
    , ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMEStAMP
    , source_file TEXT
    , PRIMARY KEY (order_id, region)
);

CREATE TABLE IF NOT EXISTS raw.customers_raw(
    customer_id TEXT
    , customer_name TEXT
    , email TEXT
    , region TEXT
    , registration_date DATE
    , source_file TEXT
    , ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    , PRIMARY KEY (customer_id, region)
);

CREATE TABLE IF NOT EXISTS raw.products_raw (
    product_id TEXT
    , product_name TEXT
    , category TEXT
    , subcategory TEXT
    , brand TEXT
    , cost NUMERIC
    , price NUMERIC
    , active BOOLEAN
    , source_file TEXT
    , ingestion_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    , PRIMARY KEY (product_id)
);

---    ---

--- staging ---

CREATE TABLE IF NOT EXISTS staging.sales (
    order_id TEXT
    , customer_id TEXT
    , product_id TEXT
    , region TEXT
    , order_date DATE
    , quantity INT
    , price NUMERIC
    , total_amount NUMERIC
    , ingestion_ts TIMESTAMP
    , PRIMARY KEY (order_id, region)
);

CREATE TABLE IF NOT EXISTS staging.customers (
    customer_id TEXT
    , customer_name TEXT
    , email TEXT
    , region TEXT
    , registration_date DATE
    , ingestion_ts TIMESTAMP
    , PRIMARY KEY (customer_id)
);

CREATE TABLE IF NOT EXISTS staging.products (
    product_id TEXT
    , product_name TEXT
    , category TEXT
    , subcategory TEXT
    , brand TEXT
    , cost NUMERIC
    , price NUMERIC
    , active BOOLEAN
    , ingestion_ts TIMESTAMP
    , PRIMARY KEY (product_id)
);

---    ---

--- analytics ---

CREATE TABLE IF NOT EXISTS analytics.dim_customers (
    customer_sk SERIAL PRIMARY KEY
    , customer_id TEXT
    , region TEXT
    , email_hash TEXT
    , start_date DATE
    , end_date DATE
    , is_current BOOLEAN
);

CREATE TABLE IF NOT EXISTS analytics.dim_products (
    product_sk SERIAL PRIMARY KEY,
    product_id TEXT,
    product_name TEXT,
    category TEXT,
    subcategory TEXT,
    brand TEXT,
    price NUMERIC,
    active BOOLEAN,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN
);

CREATE TABLE analytics.fact_sales (
    sale_id SERIAL PRIMARY KEY
    , order_id TEXT
    , region TEXT
    , customer_key INT
    , product_key INT
    , order_date DATE
    , quantity INT
    , price NUMERIC
    , total_amount NUMERIC
    , created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

---    ---