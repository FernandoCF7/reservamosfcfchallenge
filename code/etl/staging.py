from sqlalchemy import create_engine
import pandas as pd
import os

def transform_sales_to_stg():
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

    query = """
        SELECT *
        FROM raw.sales_raw
    """

    df = pd.read_sql(query, engine)

    # --- cleaning ---
    df = df.drop_duplicates(subset=["order_id", "region"])
    df = df.dropna(subset=["order_id", "customer_id", "product_id"])

    # --- transformación ---
    df["total_amount"] = df["quantity"] * df["price"]

    # --- load ---
    df.to_sql(
        "sales"
        , engine
        , schema=f"{os.getenv("ETL_DB_STAGING_SCHEMA")}"
        , if_exists="replace"
        , index=False
    )

def transform_products_to_stg():
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

    df = pd.read_sql("SELECT * FROM raw.products_raw", engine)

    # --- limpieza ---
    df = df.drop_duplicates(subset=["product_id"])
    df = df.dropna(subset=["product_id", "product_name"])

    # --- reglas ---
    df["price"] = df["price"].astype(float)
    df["cost"] = df["cost"].astype(float)
    df["active"] = df["active"].fillna(True)

    # --- carga ---
    df.to_sql(
        "products",
        engine,
        schema=f"{os.getenv("ETL_DB_STAGING_SCHEMA")}",
        if_exists="replace",
        index=False
    )

def transform_customers_to_stg():
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

    df = pd.read_sql("SELECT * FROM raw.customers_raw", engine)

    # --- limpieza ---
    df = df.drop_duplicates(subset=["customer_id", "region"])
    df = df.dropna(subset=["customer_id", "customer_name"])

    # normalización
    df["email"] = df["email"].str.lower()

    # --- carga ---
    df.to_sql(
        "customers",
        engine,
        schema=f"{os.getenv("ETL_DB_STAGING_SCHEMA")}",
        if_exists="replace",
        index=False
    )
