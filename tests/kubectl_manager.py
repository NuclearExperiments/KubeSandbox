import unittest
from unittest.mock import patch

from kubesandbox import config
from kubesandbox.kubeclient.kubectl_manager import KubeManager
from kubesandbox.kubeclient.model import KubeObject
from kubesandbox.planner.support import Step, DisplayMessages


class TestKubeManager(unittest.TestCase):

    @patch('kubesandbox.kubeclient.kubectl_manager.logger.info')
    @patch('kubesandbox.kubeclient.kubectl_manager.logger.debug')
    @patch('kubesandbox.config.workdir', './')
    @patch('uuid.uuid4', return_value='test-uuid')
    def test_generate_kubectl_apply_step_single_object(self, *args):
        kube_object = KubeObject(
            name='my-resource',
            kind='Deployment',
            yaml_content='---\nkind: Deployment\nmetadata:\n  name: my-resource\n---',
            namespace='my-namespace'
        )
        step = KubeManager.generate_kubectl_apply_step(kube_object)
        self.assertEqual(step.name, 'Apply Deployment for My-Resource')
        self.assertEqual(step.command, 'kubectl')
        self.assertEqual(step.args, ['apply', '-f', './test-uuid.yaml', '--namespace', 'my-namespace'])
        self.assertEqual(step.dependencies, ['kubectl'])
        self.assertEqual(step.optional, True)
        self.assertIsInstance(step.display_messages, DisplayMessages)

    @patch('kubesandbox.config.workdir', './')
    @patch('uuid.uuid4', return_value='test-uuid')
    @patch('kubesandbox.kubeclient.kubectl_manager.logger.info')
    @patch('kubesandbox.kubeclient.kubectl_manager.logger.debug')
    def test_generate_kubectl_apply_step_multiple_objects(self, *args):
        kube_objects = [
            KubeObject(
                name='my-deployment',
                kind='Deployment',
                yaml_content='---\nkind: Deployment\nmetadata:\n  name: my-deployment\n---'
            ),
            KubeObject(
                name='my-service',
                kind='Service',
                yaml_content='---\nkind: Service\nmetadata:\n  name: my-service\n---'
            )
        ]
        step = KubeManager.generate_kubectl_apply_step(kube_objects)
        self.assertEqual(step.name, 'Apply Deployment for My-Deployment')
        self.assertEqual(step.command, 'kubectl')
        self.assertEqual(step.args, ['apply', '-f', './test-uuid.yaml'])
        self.assertEqual(step.dependencies, ['kubectl'])
        self.assertEqual(step.optional, True)
        self.assertIsInstance(step.display_messages, DisplayMessages)
        self.assertIsInstance(step.on_success, Step)

    @patch('kubesandbox.kubeclient.kubectl_manager.logger.info')
    def test_write_content_to_file(self, mock_info):
        kube_object = KubeObject(
            name='my-resource',
            kind='Deployment',
            yaml_content='---\nkind: Deployment\nmetadata:\n  name: my-resource\n---'
        )
        filename = KubeManager.write_content_to_file(kube_object)
        self.assertTrue(filename.startswith(config.workdir))
        self.assertTrue(filename.endswith('.yaml'))

    @patch('kubesandbox.kubeclient.kubectl_manager.logger.info')
    @patch('kubesandbox.kubeclient.kubectl_manager.logger.debug')
    def test_kube_object_to_step_apply(self, mock_debug, mock_info):
        kube_object = KubeObject(
            name='my-resource',
            kind='Deployment',
            yaml_file='my-resource.yaml',
            namespace='my-namespace',
            display_messages={
                'ongoing_message': 'Custom ongoing message',
                'success_message': 'Custom success message',
                'failure_message': 'Custom failure message'
            }
        )
        step = KubeManager.kube_object_to_step('apply', kube_object.yaml_file, kube_object)
        self.assertEqual(step.name, 'Apply Deployment for My-Resource')
        self.assertEqual(step.command, 'kubectl')
        self.assertEqual(step.args, ['apply', '-f', 'my-resource.yaml', '--namespace', 'my-namespace'])
        self.assertEqual(step.dependencies, ['kubectl'])
        self.assertEqual(step.optional, True)
        self.assertEqual(step.display_messages.ongoing_message, 'Custom ongoing message')
        self.assertEqual(step.display_messages.success_message, 'Custom success message')
        self.assertEqual(step.display_messages.failure_message, 'Custom failure message')

    @patch('kubesandbox.kubeclient.kubectl_manager.logger.info')
    @patch('kubesandbox.kubeclient.kubectl_manager.logger.debug')
    def test_kube_object_to_step_delete(self, mock_debug, mock_info):
        kube_object = KubeObject(
            name='my-resource',
            kind='Deployment',
            yaml_file='my-resource.yaml',
            namespace='my-namespace',
            display_messages={
                'ongoing_message': 'Custom ongoing message',
                'success_message': 'Custom success message',
                'failure_message': 'Custom failure message'
            }
        )
        step = KubeManager.kube_object_to_step('delete', kube_object.yaml_file, kube_object)
        self.assertEqual(step.name, 'Delete Deployment for My-Resource')
        self.assertEqual(step.command, 'kubectl')
        self.assertEqual(step.args, ['delete', '-f', 'my-resource.yaml', '--namespace', 'my-namespace'])
        self.assertEqual(step.dependencies, ['kubectl'])
        self.assertEqual(step.optional, True)
        self.assertEqual(step.display_messages.ongoing_message, 'Custom ongoing message')
        self.assertEqual(step.display_messages.success_message, 'Custom success message')
        self.assertEqual(step.display_messages.failure_message, 'Custom failure message')

    def test_merge_steps(self):
        display_messages = DisplayMessages(
            ongoing_message='Dummy ongoing message',
            success_message='Dummy success message',
            failure_message='Dummy failure message'
        )
        apply_steps = [
            Step(name='Apply Step 1', on_success=None, display_messages=display_messages, command='ls'),
            Step(name='Apply Step 2', on_success=None, display_messages=display_messages, command='ls'),
            Step(name='Apply Step 3', on_success=None, display_messages=display_messages, command='ls')
        ]
        delete_steps = [
            Step(name='Delete Step 1', on_success=None, display_messages=display_messages, command='ls'),
            Step(name='Delete Step 2', on_success=None, display_messages=display_messages, command='ls'),
            Step(name='Delete Step 3', on_success=None, display_messages=display_messages, command='ls')
        ]
        merged_step = KubeManager.merge_steps(apply_steps, delete_steps)
        self.assertEqual(merged_step.name, 'Apply Step 1')
        self.assertEqual(merged_step.on_success.name, 'Apply Step 2')
        self.assertEqual(merged_step.on_success.on_success.name, 'Apply Step 3')
        self.assertEqual(merged_step.on_success.on_success.on_failure.name, 'Delete Step 2')
        self.assertEqual(merged_step.on_success.on_failure.name, 'Delete Step 1')
        self.assertIsNone(merged_step.on_failure)


if __name__ == '__main__':
    unittest.main()
