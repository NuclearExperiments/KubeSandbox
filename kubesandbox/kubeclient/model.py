from typing import Optional, Self

from pydantic import BaseModel, model_validator

from kubesandbox.planner.support import DisplayMessages
from kubesandbox.storage import Resource


class KubeObject(BaseModel):
    """
    Represents a Kubernetes object.

    Attributes:
        name: The name of the Kubernetes object.
        kind: The kind of the Kubernetes object.
        yaml_file: The path to the YAML file containing the Kubernetes object definition.
        yaml_content: The YAML content of the Kubernetes object definition.
        namespace: The namespace of the Kubernetes object.
        display_messages: Custom display messages for the object's deployment and deletion.
        resources: A list of resources associated with the Kubernetes object.
    """

    name: str
    kind: Optional[str] = None
    yaml_file: Optional[str] = None
    yaml_content: Optional[str] = None
    namespace: Optional[str] = None
    display_messages: Optional[DisplayMessages] = None
    resources: list[Resource] = []

    @model_validator(mode='after')
    def check_content(self) -> Self:
        """
        Validates that either yaml_file or yaml_content is provided, but not both.

        Raises:
            ValueError: If both yaml_file and yaml_content are provided or neither is provided.

        Returns:
            The validated KubeObject instance.
        """
        if bool(self.yaml_file) == bool(self.yaml_content):
            raise ValueError("Either yaml_file or yaml_content must be provided.")

        return self
