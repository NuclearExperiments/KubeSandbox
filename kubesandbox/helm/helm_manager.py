from __future__ import annotations

import logging
from typing import Any

from rich.pretty import pretty_repr

from kubesandbox.helm.model import HelmChart
from kubesandbox.planner.support import Step, DisplayMessages

logger = logging.getLogger('App.HelmManager')


class HelmManager:
    """
    A class to manage Helm charts.
    """

    def __init__(self):
        """
        Initializes the HelmManager with an empty dictionary of listed repositories.
        """
        self.listed_repositories = {}

    @classmethod
    def list_keys(cls, input_dict: dict, path: str = None) -> dict[str, Any]:
        """
        Recursively lists all keys and values in a nested dictionary.

        Args:
            input_dict: The dictionary to list keys from.
            path: The current path in the dictionary, used for building key names.

        Returns:
            A dictionary containing all keys and values from the input dictionary,
            with keys flattened based on their path in the nested structure.
        """
        output = {}
        for key, value in input_dict.items():
            if path:
                current_path = f'{path}.{key}'
            else:
                current_path = key

            if isinstance(value, dict):
                output.update(cls.list_keys(value, current_path))
            else:
                output[current_path] = value
        return output

    @classmethod
    def get_install_args(cls, helm_chart: HelmChart) -> list[str]:
        """
        Generates a list of arguments for installing a Helm chart.

        Args:
            helm_chart: The HelmChart object containing installation parameters.

        Returns:
            A list of arguments to be used with the 'helm install' command.
        """
        install_args = ['install', helm_chart.release_name, helm_chart.chart]

        if helm_chart.wait:
            logger.info(f'Will wait for Helm chart "{helm_chart.chart}" to start up.')
            install_args += ['--wait']

        if helm_chart.timeout:
            logger.info(f'Helm chart installation timeout set to {helm_chart.chart}')
            install_args += ['--timeout', f'{helm_chart.timeout}']

        if helm_chart.repository_url:
            logger.info(f'Using repository URL "{helm_chart.repository_url}"')
            install_args += ['--repo', helm_chart.repository_url]

        if helm_chart.namespace:
            logger.info(f'Using namespace "{helm_chart.namespace}"')
            install_args += ['--namespace', f'{helm_chart.namespace}', '--create-namespace']

        if helm_chart.version:
            logger.info(f'Using version "{helm_chart.version}"')
            install_args += ['--version', f'{helm_chart.version}']

        if helm_chart.values:
            logger.debug(f'Using values:\n {pretty_repr(helm_chart.values)}')
            flat_values = cls.list_keys(helm_chart.values)
            for key, value in flat_values.items():
                install_args += ['--set', f'{key}={value}']

        return install_args

    @classmethod
    def generate_chart_installation_step(cls, helm_chart: HelmChart) -> Step:
        """
        Generates a Step object representing the installation of a Helm chart.

        Args:
            helm_chart: The HelmChart object to be installed.

        Returns:
            A Step object containing the installation command and parameters.
        """
        logger.info(
            f'Generating step to install Helm chart "{helm_chart.chart}" with release name "{helm_chart.release_name}"')

        install_args = cls.get_install_args(helm_chart)

        display_messages: dict[str, str]

        display_messages = {
            'ongoing_message': f'Installing Helm chart {helm_chart.release_name.title()}',
            'success_message': f'Helm chart {helm_chart.release_name.title()} installed successfully',
            'failure_message': f'Helm chart {helm_chart.release_name.title()} installation failed',
        }

        if helm_chart.display_messages:
            display_messages.update(helm_chart.display_messages.model_dump(exclude_unset=True, exclude_none=True))

        step = Step(
            name=f'Install {helm_chart.release_name.title()}',
            display_messages=DisplayMessages.model_validate(display_messages),
            dependencies=['helm'],
            command='helm',
            args=install_args,
            optional=False,
            resources=helm_chart.resources
        )

        return step

    @classmethod
    def install_chart(cls, helm_chart: HelmChart) -> list[str]:
        """
        Generates a list of commands to install a Helm chart.

        Args:
            helm_chart: The HelmChart object to be installed.

        Returns:
            A list of commands to be executed for installing the Helm chart.
        """
        logger.info(f'Installing Helm chart "{helm_chart.chart}" with release name "{helm_chart.release_name}"')

        install_args = cls.get_install_args(helm_chart)

        return ['helm'] + install_args
