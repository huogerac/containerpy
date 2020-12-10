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

    def _get_local_image(self, image_name):
        """Returns the image when it exists locally"""
        try:
            return self.client.images.get(image_name)
        except docker.errors.ImageNotFound:
            return None

    def _initialize_image(self):
        image_name = self.task["image"]
        if self._get_local_image(image_name):
            logger.info(f"Image {image_name} already exists locally")
            return

        for line in self.client_api.pull(repository=image_name, stream=True, decode=True):
            logger.info(line.get("status"))

    def _initialize_env(self):
        self.environment.update(self.task.get("environment", {}))
        self.environment.update(self.task.get("inputs", {}))
        self.environment.update(self.task.get("outputs", {}))

    def _create_container(self):
        self.container = self.client.containers.create(
            image=self.task["image"],
            entrypoint=self.task.get("entrypoint", "tail -f /dev/null"),
            environment=self.environment,
        )

    def _execute_script(self, stdout_to=logger.info, stderr_to=logger.error):
        self.exit_code = 0
        self.container.start()

        self.execution = self.container.exec_run(self.task["script"], stream=True, demux=True)
        try:
            for stdout, stderr in self.execution.output:
                if stdout:
                    stdout_to(stdout)

                elif stderr:
                    stderr_to(stderr)
            print("fim")

        except Exception as error:
            error_msg = "CONTAINER EXEC ERROR: {}".format(str(error))
            logger.error(error_msg, exc_info=error)
            raise RuntimeError(error_msg)

    def run_task(self, task, stdout_to=None, stderr_to=None):

        logger.info("Starting container")
        self.task = task

        self._initialize_image()
        self._initialize_env()
        self._create_container()
        self._execute_script(stdout_to, stderr_to)

        self.container.stop()
        logger.info("container stopped")

        self.client.close()
        logger.info("connection stopped")

        logger.info("done")
