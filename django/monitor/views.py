from django.shortcuts import render, redirect
from .models import PipelineRun
from .services import trigger_dag
import requests
from django.http import JsonResponse
from django.conf import settings
from django.http import HttpResponse

def dashboard(request):
    runs = PipelineRun.objects.all().order_by('-created_at')
    return render(request, "monitor/dashboard.html", {"runs": runs})

def run_pipeline(request):
    if request.method == "POST":
        response = requests.post(
            "http://airflow-webserver:8080/api/v1/dags/etl_pipeline/dagRuns",
            auth=(settings.AIRFLOW_USER, settings.AIRFLOW_PASSWORD),
            json={}
        )

        data = response.json()

        PipelineRun.objects.create(
            dag_id="etl_pipeline",
            dag_run_id=data.get("dag_run_id"),
            status="running"
        )

    return redirect("dashboard")

def get_status(request, dag_run_id):
    url = f"http://airflow-webserver:8080/api/v1/dags/etl_pipeline/dagRuns/{dag_run_id}"

    response = requests.get(
        url,
        auth=(settings.AIRFLOW_USER, settings.AIRFLOW_PASSWORD)
    )

    data = response.json()
    state = data.get("state")

    # UPDATE BD
    try:
        run = PipelineRun.objects.get(dag_run_id=dag_run_id)
        run.status = state

        if state in ["success", "failed"]:
            from django.utils import timezone
            run.finished_at = timezone.now()

        run.save()
    except PipelineRun.DoesNotExist:
        pass

    return JsonResponse(data)

def run_detail(request, dag_run_id):
    run = PipelineRun.objects.get(dag_run_id=dag_run_id)

    # Obtener info del DAG run
    url = f"http://airflow-webserver:8080/api/v1/dags/{run.dag_id}/dagRuns/{dag_run_id}"

    response = requests.get(
        url,
        auth=(settings.AIRFLOW_USER, settings.AIRFLOW_PASSWORD)
    )

    dag_info = response.json() if response.status_code == 200 else {}

    # Obtener tasks
    tasks_url = f"http://airflow-webserver:8080/api/v1/dags/{run.dag_id}/dagRuns/{dag_run_id}/taskInstances"

    tasks_response = requests.get(
        tasks_url,
        auth=(settings.AIRFLOW_USER, settings.AIRFLOW_PASSWORD)
    )

    tasks = tasks_response.json().get("task_instances", []) if tasks_response.status_code == 200 else []

    return render(request, "monitor/detail.html", {
        "run": run,
        "dag_info": dag_info,
        "tasks": tasks
    })

def log_view(request, dag_run_id, task_id):
    url = f"http://airflow-webserver:8080/api/v1/dags/etl_pipeline/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/1"

    response = requests.get(
        url,
        auth=(settings.AIRFLOW_USER, settings.AIRFLOW_PASSWORD)
    )

    if response.status_code == 200:
        return HttpResponse(f"<pre>{response.text}</pre>")
    
    return HttpResponse("No se pudo obtener log")