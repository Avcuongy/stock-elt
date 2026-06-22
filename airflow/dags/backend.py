from datetime import datetime, timedelta
from airflow.providers.standard.operators.bash import BashOperator
from airflow import DAG

PROJECT_PATH = "/opt/airflow/project"
PYTHON_EXEC = f"export PYTHONPATH={PROJECT_PATH}:{PROJECT_PATH}/src && python"

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
    start_date=datetime(2026, 6, 20),
    catchup=False,
    tags=["source", "backend", "etl"],
) as dag:

    task_extract_1 = BashOperator(
        task_id="crawl_companies",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/extract/crawl_companies.py",
    )

    task_extract_2 = BashOperator(
        task_id="crawl_markets",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/extract/crawl_markets.py",
    )

    task_transform_1 = BashOperator(
        task_id="transform_others_1",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/transform/transform_others_1.py",
    )

    task_transform_2 = BashOperator(
        task_id="transform_exchanges_2",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/transform/transform_exchanges_2.py",
    )

    task_transform_3 = BashOperator(
        task_id="transform_companies_3",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/transform/transform_companies_3.py",
    )

    task_load_1 = BashOperator(
        task_id="load_others_1",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/load/load_db_others_1.py",
    )

    task_load_2 = BashOperator(
        task_id="load_exchanges_2",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/load/load_db_exchanges_2.py",
    )

    task_load_3 = BashOperator(
        task_id="load_companies_3",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/backend/load/load_db_companies_3.py",
    )

    (
        [task_extract_1, task_extract_2]
        >> task_transform_1
        >> task_transform_2
        >> task_transform_3
        >> task_load_1
        >> task_load_2
        >> task_load_3
    )
