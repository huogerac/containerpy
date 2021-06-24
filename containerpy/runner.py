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
        self.exit_code = 0

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

    def _execute_script(self, stdout_to, stderr_to):
        """Deprecated"""
        self.container.start()

        cmds = self.task["script"]
        self.execution = self.container.exec_run(cmds, stream=True, demux=True)
        try:
            for stdout, stderr in self.execution.output:
                if stdout:
                    stdout_to(stdout)

                elif stderr:
                    stderr_to(stderr)

        except docker.errors.APIError as error:
            error_msg = "ContainerPY Error: {}".format(str(error))
            logger.error(error_msg, exc_info=error)
            raise RuntimeError(error_msg)

    def _execute_script_api(self, stdout_to, stderr_to, show_commands=True):

        try:
            self.pid = 0
            self.exit_code = 0
            self.stderr = None

            stdout_to("Starting container")
            self.container.start()

            self.command = self.task["script"]
            if isinstance(self.command, str):
                self.command(self.command.split(" "))

            if show_commands:
                stdout_to("> {}".format(" ".join(self.command)))

            self.pre_exececution = self.client_api.exec_create(
                self.container.id,
                self.command,
                environment=self.environment,
            )

            self.execution = self.client_api.exec_start(
                self.pre_exececution["Id"], stream=True, demux=True
            )

            for stdout, stderr in self.execution:
                stdout_to(stdout)
                if stderr:
                    self.stderr = stderr
                    stderr_to(stderr)

            self.inspect = self.client_api.exec_inspect(self.pre_exececution["Id"])
            self.exit_code = self.inspect["ExitCode"]
            self.pid = self.inspect["Pid"]

            if self.exit_code > 0 and self.stderr is None:
                self.stderr = stdout

            stdout_to("Exit code {} (Pid: {})".format(self.exit_code, self.pid))

        except docker.errors.APIError as error:
            error_msg = "ContainerPY Error: {}".format(str(error))
            logger.error(error_msg, exc_info=error)
            raise RuntimeError(error_msg)

    def run_task(
        self,
        task,
        stdout_to=logger.info,
        stderr_to=logger.error,
        show_commands=True,
        stop_container=True,
    ):

        logger.info("Starting container")
        self.task = task

        self._initialize_image()
        self._initialize_env()
        self._create_container()
        self._execute_script_api(stdout_to, stderr_to, show_commands)

        if stop_container:
            self.container.stop()
            logger.info("container stopped")

            self.container.remove()
            logger.info("container removed")

        self.client.close()
        logger.info("connection stopped")

        logger.info("done")
