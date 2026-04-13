import requests
from requests.auth import HTTPBasicAuth

AIRFLOW_URL = "http://airflow-webserver:8080"
USERNAME = "airflow"
PASSWORD = "airflow"


def trigger_dag(dag_id="etl_pipeline"):
    url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns"

    response = requests.post(
        url,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        json={}
    )

    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Error triggering DAG: {response.text}")


def get_dag_runs(dag_id="etl_pipeline"):
    url = f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(USERNAME, PASSWORD)
    )

    if response.status_code == 200:
        return response.json()["dag_runs"]
    else:
        raise Exception(f"Error getting DAG runs: {response.text}")

def get_latest_status(dag_run_id, dag_id="etl_pipeline"):
    runs = get_dag_runs(dag_id)

    for run in runs:
        if run["dag_run_id"] == dag_run_id:
            return run["state"]

    return "unknown"