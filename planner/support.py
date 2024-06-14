from typing import Optional, Self

from pydantic import BaseModel, model_validator

from exception_classes import NoCommandSpecifiedException
from storage import Resource


class DisplayMessages(BaseModel):
    """
    Represents display messages for a step.

    Attributes:
        success_message: The message to display on successful execution of the step.
        failure_message: The message to display on failed execution of the step.
        ongoing_message: The message to display while the step is in progress.
        description: A description of the step.
        success_instructions: Instructions to be displayed after successful execution of the step.
        failure_instructions: Instructions to be displayed after failed execution of the step.
    """
    success_message: Optional[str] = None
    failure_message: Optional[str] = None
    ongoing_message: Optional[str] = None
    description: Optional[str] = None
    success_instructions: Optional[str] = None
    failure_instructions: Optional[str] = None


class Step(BaseModel):
    """
    Represents a step in a plan.

    Attributes:
        name: The name of the step.
        dependencies: A list of dependencies required for the step.
        command: The command to execute for the step.
        args: A list of arguments for the command.
        quoted_command: A quoted command to execute for the step.
        optional: Whether the step is optional.
        on_success: The step to execute if the current step succeeds.
        on_failure: The step to execute if the current step fails.
        display_messages: Display messages for the step.
        resources: A list of resources associated with the step.
        execution_effort: The total effort required for the step and its sub-steps.
    """
    name: str
    dependencies: list[str] = []
    command: Optional[str] = None
    args: list[str] = []
    quoted_command: Optional[str] = None
    optional: bool = False
    on_success: Optional['Step'] = None
    on_failure: Optional['Step'] = None
    display_messages: DisplayMessages
    resources: list[Resource] = []
    execution_effort: int = 0

    @model_validator(mode='after')
    def check_command(self) -> Self:
        """
        Validates that either "command" or "quoted_command" is specified for the step.

        Raises:
            NoCommandSpecifiedException: If neither "command" nor "quoted_command" is specified.

        Returns:
            The validated Step instance.
        """
        if not self.command and not self.quoted_command:
            raise NoCommandSpecifiedException('Neither "command" nor "quoted_command" was specified for the step.')
        return self


class InstallationSource(BaseModel):
    """
    Represents the source for installing a package.

    Attributes:
        url: The URL of the installation source.
        request_params: Optional request parameters for the installation source.
        request_headers: Optional request headers for the installation source.
        install_command: Optional command to execute for installing the package.
        requires_root: Whether the installation requires root privileges.
    """
    url: str
    request_params: Optional[dict[str, str]] = None
    request_headers: Optional[dict[str, str]] = None
    install_command: Optional[str] = None
    requires_root: bool = False
