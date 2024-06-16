from unittest.mock import patch

import pytest

from kubesandbox.helm.helm_manager import HelmManager, HelmChart
from kubesandbox.planner.support import Step, DisplayMessages


@pytest.fixture
def helm_manager():
    return HelmManager()


def test_list_keys(helm_manager):
    test_dict = {
        'level1': {
            'level2': 'value1',
            'level3': {
                'level4': 'value2'
            }
        },
        'level5': 'value3'
    }
    expected_output = {
        'level1.level2': 'value1',
        'level1.level3.level4': 'value2',
        'level5': 'value3'
    }
    assert HelmManager.list_keys(test_dict) == expected_output


def test_get_install_args_basic(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart')
    expected_args = ['install', 'my-chart', 'my-chart']
    assert HelmManager.get_install_args(helm_chart) == expected_args


def test_get_install_args_with_wait(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', wait=True)
    expected_args = ['install', 'my-chart', 'my-chart', '--wait']
    assert HelmManager.get_install_args(helm_chart) == expected_args


def test_get_install_args_with_timeout(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', timeout='300')
    expected_args = ['install', 'my-chart', 'my-chart', '--timeout', '300']
    assert HelmManager.get_install_args(helm_chart) == expected_args


def test_get_install_args_with_repository_url(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', repository_url='https://example.com/charts')
    expected_args = ['install', 'my-chart', 'my-chart', '--repo', 'https://example.com/charts']
    assert HelmManager.get_install_args(helm_chart) == expected_args


def test_get_install_args_with_namespace(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', namespace='my-namespace')
    expected_args = ['install', 'my-chart', 'my-chart', '--namespace', 'my-namespace', '--create-namespace']
    assert HelmManager.get_install_args(helm_chart) == expected_args


def test_get_install_args_with_version(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', version='1.2.3')
    expected_args = ['install', 'my-chart', 'my-chart', '--version', '1.2.3']
    assert HelmManager.get_install_args(helm_chart) == expected_args


def test_get_install_args_with_values(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', values={'key1': 'value1', 'key2': 'value2'})
    expected_args = ['install', 'my-chart', 'my-chart', '--set', 'key1=value1', '--set', 'key2=value2']
    assert HelmManager.get_install_args(helm_chart) == expected_args


def test_generate_chart_installation_step_basic(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart')
    expected_step = Step(
        name='Install My-Chart',
        display_messages=DisplayMessages(
            ongoing_message='Installing Helm chart My-Chart',
            success_message='Helm chart My-Chart installed successfully',
            failure_message='Helm chart My-Chart installation failed'
        ),
        dependencies=['helm'],
        command='helm',
        args=['install', 'my-chart', 'my-chart'],
        optional=False
    )
    assert HelmManager.generate_chart_installation_step(helm_chart) == expected_step


def test_generate_chart_installation_step_with_display_messages(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart',
                           display_messages=DisplayMessages(ongoing_message='Custom message'))
    expected_step = Step(
        name='Install My-Chart',
        display_messages=DisplayMessages(
            ongoing_message='Custom message',
            success_message='Helm chart My-Chart installed successfully',
            failure_message='Helm chart My-Chart installation failed'
        ),
        dependencies=['helm'],
        command='helm',
        args=['install', 'my-chart', 'my-chart'],
        optional=False
    )
    assert HelmManager.generate_chart_installation_step(helm_chart) == expected_step


def test_install_chart(helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart')
    expected_commands = ['helm', 'install', 'my-chart', 'my-chart']
    assert HelmManager.install_chart(helm_chart) == expected_commands


@patch('kubesandbox.helm.helm_manager.logger.info')
def test_install_chart_logging(mock_logger, helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart')
    HelmManager.install_chart(helm_chart)
    mock_logger.assert_called_once_with(
        f'Installing Helm chart "{helm_chart.chart}" with release name "{helm_chart.release_name}"')


@patch('kubesandbox.helm.helm_manager.logger.debug')
def test_get_install_args_logging_debug(mock_logger, helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', values={'key1': 'value1', 'key2': 'value2'})
    HelmManager.get_install_args(helm_chart)
    mock_logger.assert_called_once_with(f'Using values:\n {helm_chart.values}')


@patch('kubesandbox.helm.helm_manager.logger.info')
def test_get_install_args_logging_info(mock_logger, helm_manager):
    helm_chart = HelmChart(release_name='my-chart', chart='my-chart', wait=True)
    HelmManager.get_install_args(helm_chart)
    mock_logger.assert_called_once_with(f'Will wait for Helm chart "{helm_chart.chart}" to start up.')
