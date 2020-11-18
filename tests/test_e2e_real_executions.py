import logging
from containerpy.runner import DockerRunner

logger = logging.getLogger(__name__)


def test_should_run_a_simple_print(caplog):
    caplog.set_level(logging.INFO)
    task = {
        "image": "ubuntu:latest",
        "script": [
            "echo HELLO CONTAINERPY",
        ],
    }

    runner = DockerRunner()
    runner.run_task(task)

    assert "HELLO CONTAINERPY" in caplog.text


def test_should_run_a_simple_python(caplog):
    caplog.set_level(logging.INFO)
    task = {
        "image": "python:3.7.5-slim",
        "script": [
            "python",
            "-c",
            "print(40+2)",
        ],
    }

    runner = DockerRunner()
    runner.run_task(task)

    assert "42" in caplog.text


def test_should_download_a_file(caplog):
    caplog.set_level(logging.INFO)
    download_cmd = ";".join(
        [
            "apt-get update",
            "apt-get install -y wget",
            "wget https://gist.githubusercontent.com/marijn/396531/raw/188caa065e3cd319fed7913ee3eecf5eec541918/countries.txt -P /tmp",
            "wc -l /tmp/countries.txt",
        ]
    )

    task = {"image": "ubuntu:latest", "script": ["sh", "-c", download_cmd]}

    runner = DockerRunner()
    runner.run_task(task)

    assert "240 /tmp/countries.txt" in caplog.text


def test_should_set_inputs_as_env_variables(caplog):
    caplog.set_level(logging.INFO)
    task = {"image": "ubuntu:latest", "script": ["sh", "-c", "echo ${MYVAR}"], "inputs": {"MYVAR": "The value 42"}}

    runner = DockerRunner()
    runner.run_task(task)

    assert "The value 42" in caplog.text
