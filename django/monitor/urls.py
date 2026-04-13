from django.urls import path
from .views import dashboard, run_pipeline, run_detail, log_view, get_status

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('run/', run_pipeline, name='run_pipeline'),
    path('run/<str:dag_run_id>/', run_detail, name='run_detail'),
    path('log/<str:dag_run_id>/<str:task_id>/', log_view, name='log_view'),
    path('status/<str:dag_run_id>/', get_status, name='get_status'),
]
