import unittest
from pprint import pformat
from unittest.mock import patch

from helm.helm_manager import HelmManager
from helm.model import HelmChart


class TestHelmManager(unittest.TestCase):

    def test_list_keys(self):
        test_dict = {
            'key1': 'value1',
            'key2': {
                'key2_1': 'value2_1',
                'key2_2': 'value2_2'
            },
            'key3': [1, 2, 3]
        }
        expected_output = {
            'key1': 'value1',
            'key2.key2_1': 'value2_1',
            'key2.key2_2': 'value2_2',
            'key3': [1, 2, 3]
        }
        self.assertEqual(HelmManager.list_keys(test_dict), expected_output)

    def test_get_install_args_basic(self):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release'
        )
        expected_args = ['install', 'my-release', 'my-chart']
        self.assertEqual(HelmManager.get_install_args(helm_chart), expected_args)

    @patch('helm.helm_manager.logger.info')
    def test_get_install_args_with_wait(self, mock_info):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release',
            wait=True
        )
        expected_args = ['install', 'my-release', 'my-chart', '--wait']
        self.assertEqual(HelmManager.get_install_args(helm_chart), expected_args)
        mock_info.assert_called_once_with('Will wait for Helm chart "my-chart" to start up.')

    @patch('helm.helm_manager.logger.info')
    def test_get_install_args_with_timeout(self, mock_info):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release',
            timeout='300'
        )
        expected_args = ['install', 'my-release', 'my-chart', '--timeout', '300']
        self.assertEqual(HelmManager.get_install_args(helm_chart), expected_args)
        mock_info.assert_called_once_with('Helm chart installation timeout set to my-chart')

    @patch('helm.helm_manager.logger.info')
    def test_get_install_args_with_repository_url(self, mock_info):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release',
            repository_url='https://example.com/charts'
        )
        expected_args = ['install', 'my-release', 'my-chart', '--repo', 'https://example.com/charts']
        self.assertEqual(HelmManager.get_install_args(helm_chart), expected_args)
        mock_info.assert_called_once_with('Using repository URL "https://example.com/charts"')

    @patch('helm.helm_manager.logger.info')
    def test_get_install_args_with_namespace(self, mock_info):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release',
            namespace='my-namespace'
        )
        expected_args = ['install', 'my-release', 'my-chart', '--namespace', 'my-namespace', '--create-namespace']
        self.assertEqual(HelmManager.get_install_args(helm_chart), expected_args)
        mock_info.assert_called_once_with('Using namespace "my-namespace"')

    @patch('helm.helm_manager.logger.info')
    def test_get_install_args_with_version(self, mock_info):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release',
            version='1.2.3'
        )
        expected_args = ['install', 'my-release', 'my-chart', '--version', '1.2.3']
        self.assertEqual(HelmManager.get_install_args(helm_chart), expected_args)
        mock_info.assert_called_once_with('Using version "1.2.3"')

    @patch('helm.helm_manager.logger.debug')
    def test_get_install_args_with_values(self, mock_debug):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release',
            values={'key1': 'value1', 'key2': {'key2_1': 'value2_1'}}
        )
        expected_args = ['install', 'my-release', 'my-chart', '--set', 'key1=value1', '--set', 'key2.key2_1=value2_1']
        self.assertEqual(HelmManager.get_install_args(helm_chart), expected_args)
        mock_debug.assert_called_once_with(
            'Using values:\n {}'.format(pformat({'key1': 'value1', 'key2': {'key2_1': 'value2_1'}})))

    @patch('helm.helm_manager.logger.info')
    def test_generate_chart_installation_step(self, mock_info):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release'
        )
        step = HelmManager.generate_chart_installation_step(helm_chart)
        self.assertEqual(step.name, 'Install My-Release')
        self.assertEqual(step.command, 'helm')
        self.assertEqual(step.args, ['install', 'my-release', 'my-chart'])
        self.assertEqual(step.dependencies, ['helm'])
        self.assertEqual(step.optional, False)
        mock_info.assert_called_once_with(
            'Generating step to install Helm chart "my-chart" with release name "my-release"')

    @patch('helm.helm_manager.logger.info')
    def test_install_chart(self, mock_info):
        helm_chart = HelmChart(
            chart='my-chart',
            release_name='my-release'
        )
        expected_args = ['helm', 'install', 'my-release', 'my-chart']
        self.assertEqual(HelmManager.install_chart(helm_chart), expected_args)
        mock_info.assert_called_once_with('Installing Helm chart "my-chart" with release name "my-release"')


if __name__ == '__main__':
    unittest.main()
