from __future__ import annotations

import logging
import os
import uuid
from typing import Literal

import config
from kubeclient.model import KubeObject
from planner.support import Step, DisplayMessages

logger = logging.getLogger("App.KubeManager")


class KubeManager:
    """
    A class to manage Kubernetes objects using kubectl.
    """

    @classmethod
    def generate_kubectl_apply_step(cls, kube_objects: list[KubeObject] | KubeObject) -> Step:
        """
        Generates a Step object representing the application of a list of Kubernetes objects or a single object.

        Args:
            kube_objects: A list of KubeObject instances or a single KubeObject instance to be applied.

        Returns:
            A Step object containing the kubectl apply command and parameters.
        """
        if isinstance(kube_objects, KubeObject):
            kube_objects = [kube_objects]

        apply_steps = []
        delete_steps = []

        for kube_object in kube_objects:
            if kube_object.yaml_content:
                yaml_file = cls.write_content_to_file(kube_object)
                kube_object.yaml_file = yaml_file
                config.storage.temp_files.append(yaml_file)

            apply_steps.append(cls.kube_object_to_step('apply', kube_object.yaml_file, kube_object))
            delete_steps.append(cls.kube_object_to_step('delete', kube_object.yaml_file, kube_object))

        return cls.merge_steps(apply_steps, delete_steps)

    @classmethod
    def write_content_to_file(cls, kube_object: KubeObject) -> str:
        """
        Writes the YAML content of a Kubernetes object to a temporary file.

        Args:
            kube_object: The KubeObject instance containing the YAML content.

        Returns:
            The filename of the written YAML file.
        """
        logger.info(f'writing content for {kube_object.name}({kube_object.kind}) to yaml file')
        filename = os.path.join(config.workdir, f'{uuid.uuid4()}.yaml')
        with open(filename, 'w') as f:
            f.write(kube_object.yaml_content)
        logger.info(f'Generated yaml file: {filename}')
        return filename

    @classmethod
    def kube_object_to_step(cls,
                            action: Literal['apply', 'delete'],
                            yaml_file: str,
                            kube_object: KubeObject) -> Step:
        """
        Converts a KubeObject instance to a Step object representing a kubectl command.

        Args:
            action: The kubectl action to perform, either 'apply' or 'delete'.
            yaml_file: The filename of the YAML file containing the Kubernetes object definition.
            kube_object: The KubeObject instance representing the Kubernetes object.

        Returns:
            A Step object containing the kubectl command and parameters.
        """
        logger.info('Converting kubectl object to step')
        args = [action, '-f', yaml_file]

        if kube_object.namespace:
            args += ['--namespace', kube_object.namespace]

        logger.debug(f'Kubectl args: {args}')

        display_messages: dict

        if action == 'apply':
            display_messages = {
                'ongoing_message': f'Deploying {kube_object.kind or "resources"} for {kube_object.name.title()}',
                'success_message': f'Deployed {kube_object.kind or "resources"} for {kube_object.name.title()}',
                'failure_message': f'Failed to deploy {kube_object.kind or "resources"} for {kube_object.name.title()}'
            }
        else:
            display_messages = {
                'ongoing_message': f'Deleting {kube_object.kind or "resources"} for {kube_object.name.title()}',
                'success_message': f'Deleted {kube_object.kind or "resources"} for {kube_object.name.title()}',
                'failure_message': f'Failed to delete {kube_object.kind or "resources"} for {kube_object.name.title()}'
            }

        if kube_object.display_messages:
            display_messages.update(kube_object.display_messages.model_dump(exclude_unset=True, exclude_none=True))

        logger.debug(f'Display messages: {display_messages}')

        return Step(
            name=f'{action.title()} {kube_object.kind or "resources"} for {kube_object.name.title()}',
            dependencies=['kubectl'],
            optional=True,
            command='kubectl',
            args=args,
            display_messages=DisplayMessages.model_validate(display_messages),
            resources=kube_object.resources
        )

    @classmethod
    def merge_steps(cls, apply_steps: list[Step], delete_steps: list[Step]) -> Step:
        """
        Merges two lists of Step objects, creating a chain of steps with success and failure dependencies.

        Args:
            apply_steps: A list of Step objects representing the 'apply' actions.
            delete_steps: A list of Step objects representing the 'delete' actions.

        Returns:
            The first Step object in the merged chain.
        """
        for reverse_index in range(len(delete_steps) - 1, 0, -1):
            delete_steps[reverse_index].on_success = delete_steps[reverse_index - 1]

        for index in range(len(apply_steps) - 1):
            apply_steps[index].on_success = apply_steps[index + 1]
            apply_steps[index + 1].on_failure = delete_steps[index + 1].on_success

        return apply_steps[0]
