import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert
import os

def upsert_sales(df, engine):

    meta = MetaData()
    table = Table("sales_raw", meta, schema=f"{os.getenv("ETL_DB_RAW_SCHEMA")}", autoload_with=engine)

    with engine.begin() as conn:

        for _, row in df.iterrows():
            stmt = insert(table).values(**row.to_dict())
            stmt = stmt.on_conflict_do_nothing(index_elements=["order_id"])
            conn.execute(stmt)

def load_raw_sales(path, source_file):

    df = pd.read_json(path)

    # metadata
    df["source_file"] = source_file

    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

    upsert_sales(df, engine)