from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_python_step(description: str, relative_script: str) -> None:
    """Run a Python script located at `relative_script` from the repo root.

    :param description (str): A brief description of the step being executed.
    :param relative_script (str): The path to the Python script to run, relative to the repo.
    """
    script_path = REPO_ROOT / relative_script

    print("\n" + "=" * 60)
    print(description)
    print("Script:", script_path)
    print("=" * 60)

    if not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script_path}")

    subprocess.run([sys.executable, str(script_path)], check=True)
