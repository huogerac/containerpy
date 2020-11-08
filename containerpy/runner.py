import logging
import docker

logger = logging.getLogger(__name__)


class DockerRunner:

    def __init__(self):
        self.client = docker.from_env()
        self.client_api = docker.APIClient(base_url="unix://var/run/docker.sock")
        self.task = None
        self.environment = {}
        self.container = None

    def _initialize_image(self):
        for line in self.client_api.pull(repository=self.task['image'], stream=True, decode=True):
            logger.info(line.get("status"))

    def _initialize_env(self):
        for task_input in self.task.get('inputs', []):
            env_attr = '{task_input.upper()}'
            self.environment[env_attr] = self.task['inputs'].get(task_input)

    def _create_container(self):
        self.container = self.client.containers.run(
            image=self.task['image'],
            command=self.task.get('entrypoint', 'sleep infinity'),
            detach=True,
            environment=self.environment,
            working_dir=self.task.get('working_dir', '/app'),
        )

    def _execute_script(self):
        self.exit_code = 0
        for cmd in self.task['script']:
            execution = self.container.exec_run(cmd, stream=True, demux=True)
            for stdout, stderr in execution.output:
                if stdout:
                    logger.info(stdout)

                elif stderr:
                    logger.error(stderr)

    def run_task(self, task):

        logger.info("Starting container")
        self.task = task

        self._initialize_image()
        self._initialize_env()
        self._create_container()
        self._execute_script()

        self.container.stop()
        logger.info('container stopped')

        self.client.close()
        logger.info('connection stopped')

        logger.info('done')
