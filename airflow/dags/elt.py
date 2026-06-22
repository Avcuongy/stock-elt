from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_PATH = "/opt/airflow/project"
PYTHON_EXEC = f"export PYTHONPATH={PROJECT_PATH}:{PROJECT_PATH}/src && python"

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
    schedule="0 1 * * *",
    start_date=datetime(2026, 6, 14),
    catchup=False,
    tags=["warehouse", "elt"],
) as dag:

    task_extract = BashOperator(
        task_id="crawl_ohlcs",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/extract/crawl_ohlcs.py",
    )

    task_load_1 = BashOperator(
        task_id="convert_api_to_parquet",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/load/convert_api_to_parquet.py",
    )

    task_load_2 = BashOperator(
        task_id="convert_db_to_parquet",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/load/convert_db_to_parquet.py",
    )

    task_load_3 = BashOperator(
        task_id="load_to_hdfs",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/load/load_to_hdfs.py",
    )

    task_transform_1 = BashOperator(
        task_id="transform_1",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/transform/transform_1.py",
    )

    task_transform_2 = BashOperator(
        task_id="transform_2",
        bash_command=f"cd {PROJECT_PATH} && {PYTHON_EXEC} src/elt/transform/transform_2.py",
    )

    (
        task_extract
        >> [task_load_1, task_load_2]
        >> task_load_3
        >> task_transform_1
        >> task_transform_2
    )
