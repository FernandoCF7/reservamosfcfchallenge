import os
from sqlalchemy import create_engine
import pandas as pd

def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

def load_postgres(df: pd.DataFrame):
    engine = get_engine()

    # deduplicates
    df = df.drop_duplicates(subset=["order_id"])

    df.to_sql(
        "sales_raw",
        engine,
        schema=f"{os.getenv('ETL_DB_RAW_SCHEMA')}",
        if_exists="append",
        index=False
    )

    print("[LOAD] Data loaded into PostgreSQL")