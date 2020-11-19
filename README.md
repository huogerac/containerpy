# Why containerpy
To manage process tasks (script) using containers

# Overview
```
      +------------------+
      | TASK DEFINITION  |
      |(containerpy.yaml)|
      +------------------+
      |     PROCESS      |
      |                  |
    INPUTS            OUTPUT 
   (Var/env)      (stdout/stderr)
      |                  |
      |                  |
      +------------------+
      |   FILESYSTEM     |
      |(read/write files)|
      +------------------+

    Exit code
      0         Success
      >1        Error
```

# TODO
```
TASK              OUTPUT   IMAGE       EXIT CODE
- hello world       stdout   ubuntu      0              DONE
- print             stdout   python:3.8  0              DONE
- wget + wc         stdout   ubuntu      0              DONE
- env               stdout   ubuntu      0              DONE
- env + input       stdout   ubuntu      0              DONE
- input + output    stdout   ubuntu      0              DONE
- exit 1            stderr   ubuntu      1
- python something  stdout   local image 0
```



# USAGE

```python
import logging
from containerpy.runner import DockerRunner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

runner = DockerRunner()

task = {"image": "ubuntu:latest", "script": ["echo HELLO CONTAINERPY"]}
# OR
task = {"image": "ubuntu:latest", "script": ["sh", "-c", "echo ${ABC}"], "inputs": [{"ABC": "100"}] }
runner.run_task(task)
```

# TESTING

pytest
