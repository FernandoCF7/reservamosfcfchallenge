import json
import pandas as pd

def extract(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    df = pd.DataFrame(json_data)
    print(f"[EXTRACT] Loaded {len(df)} records")
    return df