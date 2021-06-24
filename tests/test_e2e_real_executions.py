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
    task = {
        "image": "ubuntu:latest",
        "script": ["sh", "-c", "echo ${MYVAR}"],
        "inputs": {"MYVAR": "The value 42"},
    }

    runner = DockerRunner()
    runner.run_task(task)

    assert "The value 42" in caplog.text


def test_should_get_use_env_variables(caplog):

    caplog.set_level(logging.INFO)
    task = {
        "image": "ubuntu:latest",
        "environment": {
            "VAR1": "VALUE1",
        },
        "script": ["sh", "-c", "echo ${VAR1}"],
    }

    runner = DockerRunner()
    runner.run_task(task)

    assert "VALUE1" in caplog.text


def test_should_get_save_output(caplog):

    caplog.set_level(logging.INFO)

    download_cmd = ";".join(
        [
            "apt-get update",
            "apt-get install -y wget",
            "wget ${TXT_FILE} -O ${OUTPUT_FILE}",
            "wc -l ${OUTPUT_FILE}",
        ]
    )

    task = {
        "image": "ubuntu:latest",
        "inputs": {
            "TXT_FILE": "https://gist.githubusercontent.com/marijn/396531/raw/188caa065e3cd319fed7913ee3eecf5eec541918/countries.txt",
        },
        "outputs": {"OUTPUT_FILE": "/tmp/countries_jun2021.txt"},
        "script": ["sh", "-c", download_cmd],
    }

    runner = DockerRunner()
    runner.run_task(task)

    assert "240 /tmp/countries_jun2021.txt" in caplog.text


def test_should_stop_after_exit_code_gt_zero(caplog):

    caplog.set_level(logging.INFO)

    download_cmd = ";".join(
        [
            "echo ABC",
            "echo DEF",
            "exit 1",
            "echo NOT_EXECUTED",
        ]
    )

    task = {
        "image": "ubuntu:latest",
        "script": ["sh", "-c", download_cmd],
    }

    runner = DockerRunner()
    runner.run_task(task, show_commands=False)

    assert "ABC" in caplog.text
    assert "DEF" in caplog.text
    assert "Exit code 1" in caplog.text
    assert "NOT_EXECUTED" not in caplog.text


def test_should_save_errors_at_the_stderr(caplog):

    caplog.set_level(logging.INFO)

    download_cmd = ";".join(
        [
            "echo ABC",
            "echo ERRORviaECHO 1>&2",
            "exit 1",
        ]
    )

    task = {
        "image": "ubuntu:latest",
        "script": ["sh", "-c", download_cmd],
    }

    errors = []

    def save_error_messages(value):
        errors.append(value)

    runner = DockerRunner()
    runner.run_task(task, stderr_to=save_error_messages)

    assert "ABC" in caplog.text
    assert runner.stderr == b"ERRORviaECHO\n"
    assert errors == [b"ERRORviaECHO\n"]


def test_should_get_exit_code_126_for_invalid_command(caplog):

    caplog.set_level(logging.INFO)

    task = {
        "image": "ubuntu:latest",
        "script": [
            "blah",
        ],
    }

    runner = DockerRunner()
    runner.run_task(task)

    assert "OCI runtime exec failed: exec failed: container_linux.go" in caplog.text
    assert (
        'starting container process caused: exec: "blah": executable file not found in $PATH: unknown'
        in caplog.text
    )
    assert runner.exit_code == 126
    assert (
        runner.stderr
        == b'OCI runtime exec failed: exec failed: container_linux.go:367: starting container process caused: exec: "blah": executable file not found in $PATH: unknown\r\n'
    )
