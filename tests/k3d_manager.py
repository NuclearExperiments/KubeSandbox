import unittest
from unittest.mock import patch

import config
from k3d.manager import K3dManager
from k3d.model import ClusterConfig
from planner.support import Step, DisplayMessages

k3d_yaml_regex = r'k3d-config-\d+.yaml'


class TestK3dManager(unittest.TestCase):

    @patch('k3d.manager.logger.info')
    def test_get_loadbalancer_config_with_loadbalancer(self, mock_info):
        loadbalancer = (8080, 8443)
        expected_config = [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ]
        self.assertEqual(K3dManager.get_loadbalancer_config(loadbalancer), expected_config)
        mock_info.assert_called_once_with(f'Generating loadbalancer config for mapping {loadbalancer}')

    @patch('k3d.manager.logger.info')
    def test_get_loadbalancer_config_without_loadbalancer(self, mock_info):
        self.assertEqual(K3dManager.get_loadbalancer_config(None), [])
        mock_info.assert_called_once_with('Generating loadbalancer config for mapping None')

    @patch('k3d.manager.logger.info')
    def test_get_nodeport_config(self, mock_info):
        nodeports = 3
        expected_config = [
            {'port': '32000', 'nodeFilters': ['server:0']},
            {'port': '32001', 'nodeFilters': ['server:0']},
            {'port': '32002', 'nodeFilters': ['server:0']}
        ]
        self.assertEqual(K3dManager.get_nodeport_config(nodeports), expected_config)
        mock_info.assert_called_once_with(f'Generating nodeport config for {nodeports} ports.')

    def test_prepare_cluster_basic(self):
        step = K3dManager.prepare_cluster(cluster_name='sandbox', registry='reg:41953')
        self.assertEqual(step.name, 'Create cluster')
        self.assertEqual(step.command, 'k3d')
        self.assertEqual(len(step.args), 4)
        self.assertEqual(step.args[:3], ['cluster', 'create', '--config'])
        self.assertRegex(step.args[3], k3d_yaml_regex)
        self.assertEqual(step.dependencies, ['k3d'])
        self.assertFalse(step.optional)
        self.assertIsInstance(step.display_messages, DisplayMessages)
        self.assertIsInstance(step.on_success, Step)

    def test_prepare_cluster_with_agents(self):
        step = K3dManager.prepare_cluster(cluster_name='sandbox', agents=2, registry='reg:41953')
        self.assertEqual(step.name, 'Create cluster')
        self.assertEqual(step.command, 'k3d')
        self.assertEqual(step.args[:3], ['cluster', 'create', '--config'])
        self.assertRegex(step.args[3], k3d_yaml_regex)
        self.assertEqual(step.dependencies, ['k3d'])
        self.assertEqual(step.optional, False)
        self.assertIsInstance(step.display_messages, DisplayMessages)
        self.assertIsInstance(step.on_success, Step)

    def test_prepare_cluster_with_loadbalancer(self):
        step = K3dManager.prepare_cluster(cluster_name='sandbox', loadbalancer=(8080, 8443), registry='reg:41953')
        self.assertEqual(step.name, 'Create cluster')
        self.assertEqual(step.command, 'k3d')
        self.assertEqual(step.args[:3], ['cluster', 'create', '--config'])
        self.assertRegex(step.args[3], k3d_yaml_regex)
        self.assertEqual(step.dependencies, ['k3d'])
        self.assertFalse(step.optional)
        self.assertIsInstance(step.display_messages, DisplayMessages)
        self.assertIsInstance(step.on_success, Step)

    def test_prepare_cluster_with_nodeports(self):
        step = K3dManager.prepare_cluster(cluster_name='sandbox', nodeports=3, registry='reg:41953')
        self.assertEqual(step.name, 'Create cluster')
        self.assertEqual(step.command, 'k3d')
        self.assertEqual(step.args[:3], ['cluster', 'create', '--config'])
        self.assertRegex(step.args[3], k3d_yaml_regex)
        self.assertEqual(step.dependencies, ['k3d'])
        self.assertFalse(step.optional)
        self.assertIsInstance(step.display_messages, DisplayMessages)
        self.assertIsInstance(step.on_success, Step)

    def test_prepare_cluster_without_default_ingress(self):
        step = K3dManager.prepare_cluster(cluster_name='sandbox', registry='reg:41953', use_default_ingress=False)
        self.assertEqual(step.name, 'Create cluster')
        self.assertEqual(step.command, 'k3d')
        self.assertEqual(step.args[:3], ['cluster', 'create', '--config'])
        self.assertRegex(step.args[3], k3d_yaml_regex)
        self.assertEqual(step.dependencies, ['k3d'])
        self.assertFalse(step.optional)
        self.assertIsInstance(step.display_messages, DisplayMessages)
        self.assertIsInstance(step.on_success, Step)

    def test_prepare_registry(self):
        registry = 'reg:41953'
        step = K3dManager.prepare_registry(registry)
        self.assertEqual(step.name, 'check_registry_exists')
        self.assertEqual(step.dependencies, ['docker', 'k3d', 'grep', 'kubectl'])
        self.assertEqual(step.quoted_command,
                         '[ $(k3d registry get k3d-reg --no-headers 2> /dev/null | grep -ic \'^k3d-reg \\+registry \\+running\') -eq 1 ]')
        self.assertEqual(step.optional, True)
        self.assertIsInstance(step.display_messages, DisplayMessages)
        self.assertIsInstance(step.on_failure, Step)

    @patch('k3d.manager.logger.info')
    @patch('k3d.manager.time.time')
    @patch('k3d.manager.os.path.join')
    def test_write_cluster_config(self, mock_join, mock_time, mock_info):
        mock_time.return_value = 1678886400
        mock_join.return_value = 'k3d-config-1678886400.yaml'
        config.storage.resources = []
        cluster_config = ClusterConfig(metadata={'name': 'sandbox'})
        filename = K3dManager.write_cluster_config(cluster_config)
        self.assertEqual(filename, 'k3d-config-1678886400.yaml')
        mock_info.assert_called_once_with('Writing cluster config to "k3d-config-1678886400.yaml"')
        self.assertEqual(len(config.storage.resources), 1)
        self.assertEqual(config.storage.resources[0].name, 'K3D Config')
        self.assertEqual(config.storage.resources[0].path, 'k3d-config-1678886400.yaml')
        self.assertEqual(config.storage.resources[0].type, 'YAML file')


if __name__ == '__main__':
    unittest.main()
