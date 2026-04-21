from celery import shared_task
import requests
from django.conf import settings
from django.utils import timezone
from .models import PipelineRun

@shared_task
def sync_pipeline_status():

    runs = PipelineRun.objects.filter(status__in=["running", "queued"])

    for run in runs:
        url = f"http://airflow-webserver:8080/api/v1/dags/{run.dag_id}/dagRuns/{run.dag_run_id}"

        try:
            response = requests.get(
                url,
                auth=(settings.AIRFLOW_USER, settings.AIRFLOW_PASSWORD),
                timeout=5
            )

            if response.status_code == 200:
                state = response.json().get("state")

                if state != run.status:
                    run.status = state

                    if state in ["success", "failed"]:
                        run.finished_at = timezone.now()

                # 🔥 PROGRESO (AHORA SÍ dentro del loop)
                tasks_url = f"http://airflow-webserver:8080/api/v1/dags/{run.dag_id}/dagRuns/{run.dag_run_id}/taskInstances"

                tasks_response = requests.get(
                    tasks_url,
                    auth=(settings.AIRFLOW_USER, settings.AIRFLOW_PASSWORD)
                )

                if tasks_response.status_code == 200:
                    tasks = tasks_response.json().get("task_instances", [])

                    total = len(tasks)
                    completed = len([t for t in tasks if t["state"] in ["success", "failed"]])

                    run.progress = int((completed / total) * 100) if total > 0 else 0

                run.save()

        except Exception as e:
            print(f"Error syncing {run.dag_run_id}: {e}")