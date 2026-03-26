import os
import time
import json
import pandas as pd
from sqlalchemy import create_engine

# --- db conection --- #
def make_db_connection(): 

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")

    # Create db-engine
    return create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    )
# ---------------- #

# --- waiting for db --- #
def waiting_for_db(engine, retries=10, delay=3):
    for tmp in range(retries):
        try:
            with engine.connect():
                print("Conexión exitosa")
                return
        except Exception as e:
            print(f"Error: {e}")
            print("Esperando conexión a DB...")
            time.sleep(delay)
    raise Exception("Error: Conexión a DB NO exitosa")
# ---------------- #

# --- data ingestion --- #
def ingestion(path):

    with open(path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    return  pd.DataFrame(json_data) # --> Use pandas dataFrame
# ---------------- #

# --- Visualize the information --- #
def preview(df_data):
    print("The json information has been loaded as pandas dataFrame:\n")
    print(f"{df_data.info()}2*\n")
    print("First 4 registers:\n")
    print(df_data.head(4))
# ---------------- #

# --- CHALLENGE --- #
def challenge(df_data):

    # --- Part 1 --- #
    # Construye un proceso que rechace eventos inválidos:
    #
    #    user_id faltante o vacío
    #    timestamp no válido en formato ISO8601
    #    phone no válido

    # **Stage**: user_id faltante o vacío
    df_data = df_data[
        df_data["user_id"].notna() # --> filter null's
        &
        (df_data["user_id"] != "") # --> filter 'whites'
    ]

    # **Stage**: timestamp no válido en formato ISO8601 (YYYY-MM-DDTHH:MM:SSZ) --> 2025-11-22T00:00:00

    regx_valid_date = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$" # --> formato ISO8601
    df_data = df_data[df_data["timestamp"].astype(str).str.match(regx_valid_date)] # --> filter no ISO8601 dates

    df_data["timestamp"] = pd.to_datetime( # --> filter no valid (true) dates
        df_data["timestamp"]
        , utc=True
        , errors="coerce"
    )
    df_data = df_data[df_data["timestamp"].notna()]

    # **Stage**: phone no válido

    # Extract 'phone' at new column (avoids iterative (for) process). In this step, take just digits too
    df_data["phone"] = (
        df_data["properties"].str.get("phone").astype(str)
        .str.replace(r"\D", "", regex=True)
    )

    regx_valid_phone = r"^\d{10}(\d{2})?$"

    df_data = df_data[ # --> filter valid phone
        df_data["phone"].isna() | 
        (df_data["phone"] == "") | 
        df_data["phone"].str.match(regx_valid_phone, na=False)
    ]

    # --- END part 1 --- #

    # --- Part 2 --- #
    # Normalice datos
    #
    #    Strings en minúsculas
    #    Asegurar que event --> ["search", "purchase"]
    #    Asegurar que ["amount", "phone, "payment_method"] --> "purchase_complete"
    #    Asegurar que ["origin", "destination", "date"] --> "search"
    #    Añadir valores por defecto donde sea necesario
    #    La salida de este paso debe ser una lista de eventos válidos listos para procesar.

    # **Pre-Stage**: extract 'properties' nested fields (new columns) --> more memory but faster; i.e. NO cicles. Here take an adventage to convert str fields as lower

    # Strings en minúsculas --> the process will consider these fiels:
        # event
        # properties
        #           origin
        #           destination
        #           payment_method

    df_data["event"] = df_data["event"].str.lower()

    # extract nested fields 
    df_data["origin"] = df_data["properties"].str.get("origin").str.lower()
    df_data["destination"] = df_data["properties"].str.get("destination").str.lower()
    df_data["payment_method"] = df_data["properties"].str.get("payment_method").str.lower()
    df_data["amount"] = df_data["properties"].str.get("amount")
    # phone --> column already exists
    df_data["date"] = df_data["properties"].str.get("date")

    # **Stage**: Asegurar que 'event' --> ["search", "purchase"]

    domain = ["search", "purchase_complete"] # --> Filter register, just take when 'event' value is in domain
    df_data = df_data[df_data["event"].isin(domain)]

    # **Stage**: Asegurar que ["amount", "phone, "payment_method"] --> "purchase_complete"

    mask_search = df_data["event"] == "search"

    mask_no_forbidden_fields = (
        df_data["amount"].isna() &
        df_data["payment_method"].isna() &
        (df_data["phone"].isna() | (df_data["phone"] == ""))
    )
    df_data = df_data[~mask_search | mask_no_forbidden_fields] # filter --> pass when is purchase_complete or 'dosent has' [amount, payment_method, phone] 

    # **Stage**:  Asegurar que ["origin", "destination", "date"] --> "search"

    mask_purchase_complete = df_data["event"] == "purchase_complete"

    mask_no_forbidden_fields = (
        df_data["origin"].isna() &
        df_data["destination"].isna() &
        df_data["date"].isna()
    )

    df_data = df_data[~mask_purchase_complete | mask_no_forbidden_fields]

    # --- END part 2 --- #

    # --- Part 3 --- #

    # A partir de los eventos válidos, genera una tabla diaria con la siguienteestructura:
    # date, user_id, searches, purchases, total_purchased_amount
    #
    # Reglas:
    # searches: número de eventos "search"
    # purchases: número de eventos "purchase_complete"
    # total_purchased_amount: suma de properties.amount para "purchase"

    # **Stage**: extract data
    df_data["date"] = df_data["timestamp"].dt.date
    df_data["is_search"] = (df_data["event"] == "search").astype(int) # --> aux
    df_data["is_purchase"] = (df_data["event"] == "purchase_complete").astype(int) # --> aux
    df_data["amount"] = pd.to_numeric(df_data["amount"], errors="coerce") # --> transfor to numeric

    # amount just in 'purchase_complete'
    df_data["purchase_amount"] = df_data["amount"].where(
        df_data["event"] == "purchase_complete", 0
    )


    # Group by user
    df_table = df_data.groupby(["date", "user_id"]).agg({
        "is_search": "sum",
        "is_purchase": "sum",
        "purchase_amount": "sum"
    }).reset_index()

    df_table.columns = [ # --> rename columns
        "date",
        "user_id",
        "searches",
        "purchases",
        "total_purchased_amount"
    ]

    return df_table
# ---------------- #

# --- Load --- #
def load(df, engine):
    df.to_sql(
        "metrics_daily",
        engine,
        if_exists="replace",
        index=False
    )
    print("Carga exitosa en la DB")
# ---------------- #

# --- main --- #
def main():
    # db connection
    engine = make_db_connection()
    waiting_for_db(engine)

    # ingestion
    current_path = os.path.dirname(os.path.abspath(__file__))
    json_data_path = os.path.join(current_path, 'source', 'events.json')

    df_data = ingestion(json_data_path)

    # data pre-visualization
    preview(df_data)

    # transformation
    df_result = challenge(df_data)

    # load
    load(df_result, engine)
# ---------------- #

if __name__ == "__main__":
    main()