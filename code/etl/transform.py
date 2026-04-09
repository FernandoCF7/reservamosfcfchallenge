import pandas as pd

def transform(df_data: pd.DataFrame) -> pd.DataFrame:

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

    print(f"[TRANSFORM] Generated {len(df_table)} rows")

    return df_table