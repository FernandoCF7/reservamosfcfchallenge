from django.db import models

class PipelineRun(models.Model):

    dag_id = models.CharField(max_length=100, default="etl_pipeline")
    dag_run_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.dag_id} | {self.dag_run_id} | {self.status}"