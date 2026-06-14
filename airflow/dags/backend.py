from datetime import datetime, timedelta
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PROJECT_PATH = "/path/to/your/stock-elt"
PYTHON_EXEC = f"{PROJECT_PATH}/.venv/Scripts/python"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="backend_etl",
    default_args=default_args,
    description="Crawl API and Load into MySQL Source Database",
    schedule="0 1 1 * *",
    start_date=datetime(2026, 6, 14),
    catchup=False,
    tags=["source", "backend"],
) as dag:

    task_extract = BashOperator(
        task_id="backend_extract",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} scripts/backend/extract.py",
    )

    task_transform = BashOperator(
        task_id="backend_transform",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} scripts/backend/transform.py",
    )

    task_load = BashOperator(
        task_id="backend_load",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} scripts/backend/load.py",
    )

    task_extract >> task_transform >> task_load
