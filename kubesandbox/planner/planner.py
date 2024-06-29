import logging
import shlex
import shutil
import traceback
from typing import Literal

import httpx

from kubesandbox import config
from kubesandbox.exception_classes import UnknownPackageException, InstallationFailedException, \
    ExecutionFailureException
from kubesandbox.planner.display import RichDisplay
from kubesandbox.planner.support import Step, InstallationSource
from kubesandbox.shellclient.base_shell import Shell, ProcessResult
from kubesandbox.storage import CommandOutput, ReportNote

logger = logging.getLogger('App.Planner')


class ExecutionPlanner:
    """
    A class to manage the execution of a plan consisting of steps.

    Attributes:
        steps: A list of Step objects representing the plan.
        installation_sources: A dictionary mapping package names to their installation sources.
        _shell: An instance of the Shell class for executing commands.
        _display: An instance of the RichDisplay class for displaying information.
        progress_id: The ID of the progress bar in the display.
        current_step_total_effort: The total effort required for the current step.
        current_step_spent_effort: The effort spent on the current step.
    """

    def __init__(self, steps: list[Step], installation_sources: dict[str, InstallationSource] = {}):
        self.steps: list[Step] = steps
        self._shell: Shell = Shell()
        self._display: RichDisplay = RichDisplay('KubeSandbox')
        self.installation_sources: dict[str, InstallationSource] = installation_sources
        self.progress_id: int = 0
        self.current_step_total_effort: int = 0
        self.current_step_spent_effort: int = 0

    def __download_package_installation_script(self, package: str) -> str:
        """
        Downloads the installation script for a package from its source.

        Args:
            package: The name of the package.

        Returns:
            The installation script as a string.

        Raises:
            InstallationFailedException: If the script download fails.
        """
        logger.info(
            f'Downloading script for package "{package}" from "{self.installation_sources[package].url}"')

        response = httpx.get(
            url=self.installation_sources[package].url,
            params=self.installation_sources[package].request_params,
            headers=self.installation_sources[package].request_headers
        )
        logger.debug(f'Headers - {response.headers}\nStatus code - {response.status_code}\n'
                     f'Text - {response.text[0:100]}')

        if 300 <= response.status_code or response.status_code < 200:
            self._display.add_item_to_logs(f'Failed to download script for {package}', item_type='error')
            raise InstallationFailedException(f'Failed to download script for package "{package}"')

        return response.text

    def __execute_package_installation_script(self, package: str, installation_script: str):
        """
        Executes the installation script for a package.

        Args:
            package: The name of the package.
            installation_script: The installation script as a string.

        Raises:
            InstallationFailedException: If the script execution fails.
        """
        result = self._shell.execute_command(direct_command=f'bash -c {shlex.quote(installation_script)}')
        if result.exit_code != 0:
            logger.info('Installation failed')
            self._display.add_item_to_logs('Installation failed', item_type='error')
            raise InstallationFailedException(f'Failed to install package "{package}"')
        else:
            logger.info(f'{package.title()} installed successfully')
            self._display.add_item_to_logs(f'{package.title()} installed successfully', item_type='success')
            self._display.advance_progress_bar(self.progress_id, 1)

    def __install_package(self, package: str):
        """
        Installs a package from its source.

        Args:
            package: The name of the package.

        Raises:
            UnknownPackageException: If no installation source is available for the package.
            InstallationFailedException: If the package installation fails.
        """
        if package not in self.installation_sources:
            self._display.add_item_to_logs('No installation source available for the package ' + package,
                                           item_type='error')
            raise UnknownPackageException(f'No installation source available for the package {package}')

        logger.info(f'Installing package {package}')
        self._display.add_item_to_logs(f'Downloading installation script for package {package}',
                                       item_type='loading')

        installation_script = self.__download_package_installation_script(package)

        self._display.add_item_to_logs(f'Installing {package}', item_type='loading')

        self.__execute_package_installation_script(package, installation_script)

    def __install_packages(self, packages: set[str]):
        """
        Installs a set of packages.

        Args:
            packages: The set of packages to install.

        Raises:
            ExecutionFailureException: If package installation requires root privileges.
            InstallationFailedException: If package installation is aborted by the user.
        """
        try:
            print('The following packages are missing from the system:\n  - ' +
                  '\n  - '.join(packages) +
                  '\n\nPlease provide root access to install them or press Ctrl + C to exit and '
                  'install manually.\n')
            if self._shell.execute_command(direct_command='sudo ls').exit_code != 0:
                raise ExecutionFailureException('Package installation requires root privileges')
        except KeyboardInterrupt:
            raise InstallationFailedException('Package installation aborted by user')

        self._display.start()

        self._display.add_item_to_logs('Installing packages', item_type='heading')
        for package in packages:
            try:
                self.__install_package(package)
            except Exception as e:
                self._display.add_item_to_logs(traceback.format_exc(), item_type='error')
                self._display.stop()
                raise e

    def __get_missing_dependencies(self) -> set[str]:
        """
        Gets the set of missing dependencies for all steps in the plan.

        Returns:
            A set of missing dependencies.
        """
        dependencies = set()
        for step in self.steps:
            for dependency in step.dependencies:
                if not shutil.which(dependency):
                    dependencies.add(dependency)
        return dependencies

    def __get_step_effort(self, step: Step) -> int:
        """
        Calculates the total effort required for a step and its sub-steps.

        Args:
            step: The Step object.

        Returns:
            The total effort required for the step.
        """
        effort = 1

        if step.on_success:
            effort += self.__get_step_effort(step.on_success)

        if step.on_failure:
            effort += self.__get_step_effort(step.on_failure)

        step.execution_effort = effort
        return effort

    def __get_plan_effort(self) -> int:
        """
        Calculates the total effort required for the entire plan.

        Returns:
            The total effort required for the plan.
        """
        return sum(self.__get_step_effort(step) for step in self.steps)

    def execute(self):
        """
        Executes the plan, installing missing dependencies and executing steps.

        Raises:
            ExecutionFailureException: If a step fails and is not optional.
        """
        logger.info('Checking for missing dependencies')
        dependencies = self.__get_missing_dependencies()

        plan_effort = self.__get_plan_effort() + len(dependencies)
        self.progress_id = self._display.add_progress_bar('Progress', plan_effort)
        logger.info(f'Plan effort: {plan_effort}')

        if dependencies:
            logger.info(f'Missing dependencies: {dependencies}')
            self.__install_packages(dependencies)
        else:
            logger.info('No missing dependencies found')
            self._display.start()

        logger.info('Executing steps')

        for step in self.steps:
            self.current_step_total_effort = step.execution_effort
            logger.debug(f'Effort required for the step "{step.name}": {self.current_step_total_effort}')
            self.__execute_step(step)
            logger.debug(f'Effort spent on the step "{step.name}": {self.current_step_spent_effort}')
            self.__rectify_progress()

        self._display.stop()

    def __execute_step(self, step: Step, step_type: Literal['parent', 'success_child', 'failure_child'] = 'parent'):
        """
        Executes a step in the plan.

        Args:
            step: The Step object to execute.
            step_type: The type of step, either 'parent', 'success_child', or 'failure_child'.

        Raises:
            ExecutionFailureException: If the step fails and is not optional.
        """
        self.__update_display_for_step_start(step, step_type)

        if step.command:
            command = [step.command] + step.args
            result = self._shell.execute_command(command=command)
        elif step.quoted_command:
            result = self._shell.execute_command(direct_command=step.quoted_command)

        self._display.advance_progress_bar(self.progress_id, 1)
        self.current_step_spent_effort += 1

        config.storage.outputs.append(CommandOutput(
            title=step.name,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code
        ))

        if result.exit_code == 0:
            self.__on_step_success(step)
        else:
            self.__on_step_failure(step, result)

    def __on_step_failure(self, step: Step, result: ProcessResult) -> None:
        """
        Handles the failure of a step.

        Args:
            step: The Step object that failed.
            result: The ProcessResult object containing the output of the failed step.

        Raises:
            ExecutionFailureException: If the step failed and is not optional.
        """
        logger.info('Step failed')
        self._display.add_item_to_logs(step.display_messages.failure_message, item_type='error')
        self._display.set_details_message(f'{result.stdout}\n{result.stderr}'[:1000], print_raw=True)

        if step.display_messages.failure_instructions:
            config.storage.notes.append(
                ReportNote(
                    message=step.display_messages.failure_instructions
                )
            )

        if step.on_failure:
            logger.info('Executing on_failure callback')
            self.__execute_step(step.on_failure, step_type='failure_child')
        if not step.optional:
            self._display.stop()
            raise ExecutionFailureException(f'Step "{step.name}" failed\n\n{step.display_messages.failure_message}\n\n')

    def __on_step_success(self, step: Step):
        """
        Handles the success of a step.

        Args:
            step: The Step object that succeeded.
        """
        logger.info('Step succeeded')
        self._display.add_item_to_logs(step.display_messages.success_message, item_type='success')

        if step.display_messages.success_instructions:
            config.storage.notes.append(
                ReportNote(
                    message=step.display_messages.success_instructions
                )
            )
        if step.resources:
            config.storage.resources.extend(step.resources)

        if step.on_success:
            logger.info('Executing on_success callback')
            self.__execute_step(step.on_success, step_type='success_child')

    def __update_display_for_step_start(self, step: Step, step_type: str) -> None:
        """
        Updates the display to reflect the start of a step.

        Args:
            step: The Step object to be executed.
            step_type: The type of step, either 'parent', 'success_child', or 'failure_child'.
        """
        logger.info(f'Executing step {step_type} "{step.name}"')
        if step_type == 'parent':
            self._display.add_item_to_logs(step.name.title(), item_type='heading')

        if step.display_messages.description:
            logger.debug('Description available')
            self._display.set_details_message(step.display_messages.description)

        self._display.add_item_to_logs(step.display_messages.ongoing_message, item_type='loading')

    def __rectify_progress(self):
        """
        Rectifies the progress bar if the effort spent on the current step is less than the total effort required.
        """
        if self.current_step_total_effort > self.current_step_spent_effort:
            logger.debug(f'Rectifying progress by {self.current_step_total_effort - self.current_step_spent_effort}')
            self._display.advance_progress_bar(
                task_id=self.progress_id,
                advance_by=self.current_step_total_effort - self.current_step_spent_effort)
        else:
            logger.debug('No rectification required')
        self.current_step_spent_effort = 0
