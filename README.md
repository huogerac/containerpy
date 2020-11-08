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
- println           stdout   python:3.8  0
- wget + wc         stdout   ubuntu      0
- env               stdout   ubuntu      0
- env + input       stdout   ubuntu      0
- input + output    stdout   ubuntu      0
- exit 1            stderr   ubuntu      1
- python something  stdout   local image 0
```



# USAGE

import logging
from containerpy.runner import DockerRunner

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

runner = DockerRunner()

task = {"image": "ubuntu:latest", "script": ["echo HELLO CONTAINERPY"]}
runner.run_task(task)


# TESTING

pytest
