from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_PATH = "/opt/airflow/project"
PYTHON_EXEC = "python"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="elt_main",
    default_args=default_args,
    description="ELT",
    schedule="*/50 * * * *",
    start_date=datetime(2026, 6, 14),
    catchup=False,
    tags=["warehouse", "elt"],
) as dag:

    task_extract = BashOperator(
        task_id="elt_extract",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} scripts/elt/extract.py",
    )

    task_load = BashOperator(
        task_id="elt_load",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} scripts/elt/load.py",
    )

    task_transform = BashOperator(
        task_id="elt_transform",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} scripts/elt/transform.py",
    )

    task_extract >> task_load >> task_transform
