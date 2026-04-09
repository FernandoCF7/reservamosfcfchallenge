import os
from sqlalchemy import create_engine
import pandas as pd

def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:5432/{os.getenv('DB_NAME')}"
    )

def load_postgres(df: pd.DataFrame):
    engine = get_engine()

    df.to_sql(
        "metrics_daily",
        engine,
        schema=f"{os.getenv('DB_SCHEMA')}",
        if_exists="replace",
        index=False
    )

    print("[LOAD] Data loaded into PostgreSQL")