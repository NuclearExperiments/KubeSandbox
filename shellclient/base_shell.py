import logging
import os
import platform
import shlex
import shutil
import subprocess

logger = logging.getLogger('Shell')


class ProcessResult:
    """
    Represents the result of a process execution.

    Attributes:
        exit_code: The exit code of the process.
        stdout: The standard output of the process.
        stderr: The standard error output of the process.
    """

    def __init__(self, exit_code: int, stdout: str, stderr: str):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def __eq__(self, other):
        if isinstance(other, ProcessResult):
            return self.exit_code == other.exit_code and self.stdout == other.stdout and self.stderr == other.stderr
        return False


class NoCommandException(Exception):
    """
    Raised when no command is specified for execution.
    """
    pass


class Shell:
    """
    A class for executing shell commands.

    Attributes:
        platform: The current operating system platform.
    """
    def __init__(self):
        self.platform = Shell.get_platform()

    @staticmethod
    def check_root() -> bool:
        """
        Checks if the current process is running as root.

        Returns:
            True if the process is running as root, False otherwise.
        """
        return os.geteuid() == 0

    @staticmethod
    def execute_command(command: list[str] = None, direct_command: str = None) -> ProcessResult:
        """
        Executes a shell command.

        Args:
            command: A list of strings representing the command and its arguments.
            direct_command: A string representing the command to execute directly.

        Returns:
            A ProcessResult object containing the exit code, standard output, and standard error output of the process.

        Raises:
            NoCommandException: If neither command nor direct_command is specified.
        """
        if not command and not direct_command:
            raise NoCommandException('No command to execute')

        if direct_command:
            logger.info(f'Executing command: "{direct_command}"')
            process = subprocess.Popen(direct_command, shell=True, stdout=subprocess.PIPE, text=True)
            stdout = process.stdout.read() if process.stdout else ''
            stderr = process.stderr.read() if process.stderr else ''
            process.communicate()
            exit_code = process.returncode
            logger.info(f'Command exited with code {exit_code}. \nStdout: {stdout}. \nStderr: {stderr}')
            return ProcessResult(exit_code=exit_code, stdout=stdout, stderr=stderr)
        else:
            logger.info(f'Executing command: "{shlex.join(command)}"')
            process = subprocess.run(command, shell=False, capture_output=True, text=True)
            logger.info(
                f'Command exited with code {process.returncode}. \nStdout: {process.stdout}. \nStderr: {process.stderr}')
            return ProcessResult(exit_code=process.returncode, stdout=process.stdout, stderr=process.stderr)

    # @abstractmethod
    # def get_root_status(self) -> bool:
    #     pass

    @staticmethod
    def get_platform() -> str:
        """
        Determines the current operating system platform.

        Returns:
            The name of the current platform.
        """
        logger.info('Checking current platform')
        platform_str = platform.platform().lower()

        if platform_str.count('ubuntu') > 0:
            current_platform = 'ubuntu'
        elif platform_str.count('debian') > 0:
            current_platform = 'debian'
        elif platform_str.count('fedora') > 0:
            current_platform = 'fedora'
        elif platform_str.count('windows') > 0:
            current_platform = 'windows'
        # elif platform_str.count('linux') > 0 and platform_str.count('wsl') > 0:
        #     platform_str = 'wsl'
        else:
            logger.info('Couldn\'t determine current platform.')
            current_platform = Shell.get_platform_using_package_manager()

        logger.info(f'Current platform is "{current_platform}"')

        return current_platform

    @staticmethod
    def get_platform_using_package_manager() -> str:
        """
        Determines the current platform using the package manager.

        Returns:
            The name of the current platform.
        """
        logger.info('Checking current platform using package manager')
        if shutil.which('apt'):
            return 'debian'
        elif shutil.which('dnf'):
            return 'fedora'
        elif shutil.which('apk'):
            return 'alpine'
        elif shutil.which('pacman'):
            return 'arch'
        elif shutil.which('emerge'):
            return 'gentoo'
        else:
            return 'unknown'
