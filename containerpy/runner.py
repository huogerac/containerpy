import logging
import requests
import docker

_8MB = 8192
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

    def _download_image(self, image_url, save_to="/tmp"):

        print("Downloading: ", image_url)
        image_name = image_url.split("?")[0].split("/")[-1]
        target_path = f"{save_to}/{image_name}"

        with requests.get(image_url, stream=True) as data:
            data.raise_for_status()
            with open(target_path, "wb") as target_file:
                for chunk in data.iter_content(chunk_size=_8MB):
                    target_file.write(chunk)

        self.task["inputs"]["_image_path_local"] = target_path
        print("Image saved to: ", target_path)

    def _load_local_image(self, image_tar_path):
        """Load and image file (tar)"""
        with open(image_tar_path, "rb") as tar_file:
            self.client.images.load(tar_file)

    def _initialize_image(self):
        image_name = self.task["image"]
        if self._get_local_image(image_name):
            logger.info(f"Image {image_name} already exists locally")
            return

        _inputs = self.task.get("inputs", {})
        if _inputs.get("_image_path"):
            logger.info(f"Creating image from file: {_inputs.get('_image_path')}")
            self._download_image(_inputs.get("_image_path"))
            logger.info("Download completed")
            self._load_local_image(self.task["inputs"]["_image_path_local"])
            logger.info("Image built")
            return

        for line in self.client_api.pull(
            repository=image_name, stream=True, decode=True
        ):
            logger.info(line.get("status"))

    def _initialize_env(self):
        self.environment.update(self.task.get("environment", {}))
        self.environment.update(self.task.get("inputs", {}))
        self.environment.update(self.task.get("outputs", {}))

    def _create_container(self):

        # self.container = self.client.containers.create(
        #     image=self.task["image"],
        #     entrypoint=self.task.get("entrypoint", "tail -f /dev/null"),
        #     environment=self.environment,
        # )
        command = self.task.get("entrypoint", "tail -f /dev/null")
        self.container = self.client.containers.run(
            image=self.task["image"],
            entrypoint=command,
            detach=True,
            environment=self.environment,
            network_mode="host",
        )

    def _execute_script(self, stdout_to=logger.info, stderr_to=logger.error):
        self.exit_code = 0
        self.container.start()

        self.execution = self.container.exec_run(
            self.task["script"], stream=True, demux=True
        )
        try:
            for stdout, stderr in self.execution.output:
                if stdout:
                    stdout_to(stdout)

                elif stderr:
                    stderr_to(stderr)
            print("fim execution")

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

        self.container.remove()
        logger.info("container removed")

        self.client.close()
        logger.info("connection stopped")

        logger.info("done")
