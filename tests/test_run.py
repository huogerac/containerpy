import logging
from containerpy.runner import DockerRunner

logger = logging.getLogger(__name__)


def test_should_run_a_simple_print(caplog):
    caplog.set_level(logging.INFO)
    task = {
        "image": "ubuntu:latest",
        "script": [
            "echo HELLO CONTAINERPY",
        ]
    }

    runner = DockerRunner()
    runner.run_task(task)
    
    assert "HELLO CONTAINERPY" in caplog.text
