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
- hello world       stdout   ubuntu      0
- println           stdout   python:3.8  0
- wget + wc         stdout   ubuntu      0
- env               stdout   ubuntu      0
- env + input       stdout   ubuntu      0
- input + output    stdout   ubuntu      0
- exit 1            stderr   ubuntu      1
- python something  stdout   local image 0
```