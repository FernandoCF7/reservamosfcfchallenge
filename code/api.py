from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
import os

app = FastAPI()

# --- db conection --- #
def make_db_connection():

    DB_USER = os.getenv("ETL_DB_USER")
    DB_PASSWORD = os.getenv("ETL_DB_PASSWORD")
    DB_HOST = os.getenv("ETL_DB_HOST")
    DB_NAME = os.getenv("ETL_DB_NAME")

    # Create db-engine
    return create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    )
# ---------------- #


@app.get("/daily_stats")
def get_daily_stats(date: str = Query(...)):
    engine = make_db_connection()

    query = text("""
        SELECT 
            date
            , COUNT(DISTINCT user_id) AS total_users
            , SUM(searches) AS total_searches
            , SUM(purchases) AS total_purchases
            , SUM(total_purchased_amount) AS total_purchased_amount
        FROM metrics_daily
        WHERE date = :date
        GROUP BY date
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"date": date}).fetchone()

    if not result:
        return {"message": "No data for this date"}

    return {
        "date": str(result.date),
        "total_users": result.total_users,
        "total_searches": int(result.total_searches or 0),
        "total_purchases": int(result.total_purchases or 0),
        "total_purchased_amount": float(result.total_purchased_amount or 0)
    }