from sqlalchemy import create_engine, text
import pandas as pd
import os
from datetime import datetime
import hashlib

def load_dim_customers_scd2():
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

    df_stg = pd.read_sql(f"SELECT * FROM {os.getenv("ETL_DB_STAGING_SCHEMA")}.customers", engine)

    with engine.begin() as conn:

        for _, row in df_stg.iterrows():

            customer_id = row["customer_id"]

            email_hash = hashlib.md5(row["email"].encode()).hexdigest()

            # 1. buscar registro actual
            current = conn.execute(text(f"""
                SELECT * FROM {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_customers
                WHERE customer_id = :customer_id
                AND is_current = TRUE
            """), {"customer_id": customer_id}).fetchone()

            # --- CASO 1: no existe ---
            if current is None:
                conn.execute(text(f"""
                    INSERT INTO {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_customers (
                        customer_id, region, email_hash,
                        start_date, end_date, is_current
                    ) VALUES (
                        :customer_id, :region, :email_hash,
                        :start_date, NULL, TRUE
                    )
                """), {
                    **row,
                    "start_date": row["registration_date"]
                })

            # --- CASO 2 y 3 ---
            else:
                changed = (
                    current.region != row["region"] or
                    current.email_hash != email_hash
                )

                # CASO 2: no cambió
                if not changed:
                    continue

                # CASO 3: cambió → cerrar + insertar

                # cerrar registro actual
                conn.execute(text(f"""
                    UPDATE {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_customers
                    SET end_date = :end_date,
                        is_current = FALSE
                    WHERE customer_id = :customer_id
                    AND is_current = TRUE
                """), {
                    "customer_id": customer_id,
                    "end_date": row["registration_date"]
                })

                # insertar nuevo
                conn.execute(text(f"""
                    INSERT INTO {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_customers (
                        customer_id, region, email_hash,
                        start_date, end_date, is_current
                    ) VALUES (
                        :customer_id, :region, :email_hash,
                        :start_date, NULL, TRUE
                    )
                """), {
                    **row,
                    "start_date": row["registration_date"]
                })

def load_dim_products_scd2():

    engine = create_engine(
        f"postgresql://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}"
        f"@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

    df_stg = pd.read_sql("SELECT * FROM staging.products", engine)

    df_dim = pd.read_sql(f"""
        SELECT * FROM {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_products
        WHERE is_current = TRUE
    """, engine)

    for _, row in df_stg.iterrows():

        existing = df_dim[
            df_dim["product_id"] == row["product_id"]
        ]

        if existing.empty:
            # 🆕 nuevo producto
            engine.execute(f"""
                INSERT INTO {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_products
                (product_id, product_name, category, subcategory, brand, price, active, start_date, end_date, is_current)
                VALUES (
                    '{row.product_id}', '{row.product_name}', '{row.category}',
                    '{row.subcategory}', '{row.brand}', {row.price}, {row.active},
                    '1900-01-01', NULL, TRUE
                )
            """)
        else:
            current = existing.iloc[0]

            # detectar cambios importantes
            if (
                current["price"] != row["price"]
                or current["brand"] != row["brand"]
                or current["active"] != row["active"]
            ):
                # cerrar registro actual
                engine.execute(f"""
                    UPDATE {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_products
                    SET end_date = CURRENT_DATE, is_current = FALSE
                    WHERE product_id = '{row.product_id}'
                    AND is_current = TRUE
                """)

                # insertar nueva versión
                engine.execute(f"""
                    INSERT INTO {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_products
                    (product_id, product_name, category, subcategory, brand, price, active, start_date, end_date, is_current)
                    VALUES (
                        '{row.product_id}', '{row.product_name}', '{row.category}',
                        '{row.subcategory}', '{row.brand}', {row.price}, {row.active},
                        '1900-01-01', NULL, TRUE
                    )
                """)

def load_fact_sales():

    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('ETL_DB_USER')}:{os.getenv('ETL_DB_PASSWORD')}@{os.getenv('ETL_DB_HOST')}:5432/{os.getenv('ETL_DB_NAME')}"
    )

    df_sales = pd.read_sql(f"SELECT * FROM {os.getenv("ETL_DB_STAGING_SCHEMA")}.sales", engine)

    df_customers = pd.read_sql(f"""
        SELECT * FROM {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_customers
    """, engine)

    df_products = pd.read_sql(f"""
        SELECT * FROM {os.getenv("ETL_DB_ANALYTICS_SCHEMA")}.dim_products
    """, engine)

    fact_rows = []

    for _, sale in df_sales.iterrows():

        # 🔹 match customer SCD2
        customer_match = df_customers[
            (df_customers["customer_id"] == sale["customer_id"]) &
            (df_customers["region"] == sale["region"]) &
            (df_customers["start_date"] <= sale["order_date"]) &
            (
                (df_customers["end_date"].isna()) |
                (df_customers["end_date"] > sale["order_date"])
            )
        ]

        # 🔹 match product SCD2
        product_match = df_products[
            (df_products["product_id"] == sale["product_id"]) &
            (df_products["start_date"] <= sale["order_date"]) &
            (
                (df_products["end_date"].isna()) |
                (df_products["end_date"] > sale["order_date"])
            )
        ]

        if customer_match.empty or product_match.empty:
            continue  # o loggear error

        fact_rows.append({
            "order_id": sale["order_id"],
            "region": sale["region"],
            "customer_key": int(customer_match.iloc[0]["customer_sk"]),
            "product_key": int(product_match.iloc[0]["product_sk"]),
            "order_date": sale["order_date"],
            "quantity": sale["quantity"],
            "price": sale["price"],
            "total_amount": sale["total_amount"]
        })

    df_fact = pd.DataFrame(fact_rows)

    df_fact.to_sql(
        "fact_sales",
        engine,
        schema=os.getenv("ETL_DB_ANALYTICS_SCHEMA"),
        if_exists="append",
        index=False
    )