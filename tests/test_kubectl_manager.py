from __future__ import annotations

import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from kubesandbox import config
from kubesandbox.kubeclient.kubectl_manager import KubeManager
from kubesandbox.kubeclient.model import KubeObject
from kubesandbox.planner.support import Step, DisplayMessages


@pytest.fixture
def setup_workdir():
    config.workdir = '/tmp/kubesandbox'
    config.storage.temp_files = []
    Path(config.workdir).mkdir(parents=True, exist_ok=True)
    yield
    # Delete any generated files
    for file in config.storage.temp_files:
        if os.path.exists(file):
            os.remove(file)


@pytest.mark.parametrize("action, expected_args", [
    ('apply',
     ['apply', '-f', '/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml', '--namespace', 'test-namespace']),
    ('delete',
     ['delete', '-f', '/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml', '--namespace', 'test-namespace']),
])
@patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678'))
def test_kube_object_to_step(mock_uuid, action, expected_args, setup_workdir):
    # Test converting a KubeObject to a Step for 'apply' action
    kube_object = KubeObject(
        name='test-deployment',
        kind='Deployment',
        yaml_content='apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test-deployment\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: nginx\n  template:\n    metadata:\n      labels:\n        app: nginx\n    spec:\n      containers:\n      - name: nginx\n        image: nginx:1.14.2',
        namespace='test-namespace',
        display_messages=DisplayMessages(
            ongoing_message='Custom ongoing message',
            success_message='Custom success message',
            failure_message='Custom failure message'
        )
    )

    expected_step = Step(
        name=f'{action.capitalize()} Deployment for Test-Deployment',
        dependencies=['kubectl'],
        optional=True,
        command='kubectl',
        args=expected_args,
        display_messages=DisplayMessages(
            ongoing_message='Custom ongoing message',
            success_message='Custom success message',
            failure_message='Custom failure message'
        ),
        resources=kube_object.resources
    )

    step = KubeManager.kube_object_to_step(action, '/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml',
                                           kube_object)

    assert step.name == expected_step.name
    assert step.dependencies == expected_step.dependencies
    assert step.optional == expected_step.optional
    assert step.command == expected_step.command
    assert step.args == expected_step.args
    assert step.display_messages.model_dump() == expected_step.display_messages.model_dump()
    assert step.resources == expected_step.resources


@pytest.mark.parametrize("kube_objects, expected_step_name", [
    (
            [
                KubeObject(
                    name='test-deployment',
                    kind='Deployment',
                    yaml_content='apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test-deployment\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: nginx\n  template:\n    metadata:\n      labels:\n        app: nginx\n    spec:\n      containers:\n      - name: nginx\n        image: nginx:1.14.2'
                ),
                KubeObject(
                    name='test-service',
                    kind='Service',
                    yaml_content='apiVersion: v1\nkind: Service\nmetadata:\n  name: test-service\nspec:\n  selector:\n    app: nginx\n  ports:\n  - protocol: TCP\n    port: 80\n    targetPort: 80'
                )
            ],
            'Apply Deployment for Test-Deployment'
    )
])
@patch('uuid.uuid4', side_effect=['12345678-1234-5678-1234-567812345678', '12345678-1234-5678-1234-567812345679'])
def test_generate_kubectl_apply_step(mock_uuid, kube_objects, expected_step_name, setup_workdir):
    # Test with multiple KubeObjects
    expected_step = Step(
        args=['apply', '-f', '/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml'],
        command='kubectl',
        dependencies=['kubectl'],
        display_messages=DisplayMessages(
            failure_message='Failed to deploy Deployment for Test-Deployment',
            ongoing_message='Deploying Deployment for Test-Deployment',
            success_message='Deployed Deployment for Test-Deployment'
        ),
        name='Apply Deployment for Test-Deployment',
        on_success=Step(
            args=['apply', '-f', '/tmp/kubesandbox/12345678-1234-5678-1234-567812345679.yaml'],
            command='kubectl',
            dependencies=['kubectl'],
            display_messages=DisplayMessages(
                failure_message='Failed to deploy Service for Test-Service',
                ongoing_message='Deploying Service for Test-Service',
                success_message='Deployed Service for Test-Service'
            ),
            name='Apply Service for Test-Service',
            on_failure=Step(
                args=['delete', '-f', '/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml'],
                command='kubectl',
                dependencies=['kubectl'],
                display_messages=DisplayMessages(
                    failure_message='Failed to delete Deployment for Test-Deployment',
                    ongoing_message='Deleting Deployment for Test-Deployment',
                    success_message='Deleted Deployment for Test-Deployment'
                ),
                name='Delete Deployment for Test-Deployment',
                optional=True,
                resources=[]),
            optional=True,
            resources=[]),
        optional=True,
        resources=[]
    )

    step = KubeManager.generate_kubectl_apply_step(kube_objects)

    # Verify the generated step
    assert step.model_dump(exclude_unset=True, exclude_none=True) == expected_step.model_dump(exclude_unset=True,
                                                                                              exclude_none=True)

    # Verify the generated YAML files
    assert os.path.exists('/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml')
    with open('/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml', 'r') as f:
        assert f.read() == kube_objects[0].yaml_content
    if len(kube_objects) > 1:
        assert os.path.exists('/tmp/kubesandbox/12345678-1234-5678-1234-567812345679.yaml')
        with open('/tmp/kubesandbox/12345678-1234-5678-1234-567812345679.yaml', 'r') as f:
            assert f.read() == kube_objects[1].yaml_content


@patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678'))
def test_write_content_to_file(mock_uuid, setup_workdir):
    # Test writing content to a file
    kube_object = KubeObject(
        name='test-deployment',
        kind='Deployment',
        yaml_content='apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test-deployment\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: nginx\n  template:\n    metadata:\n      labels:\n        app: nginx\n    spec:\n      containers:\n      - name: nginx\n        image: nginx:1.14.2'
    )

    filename = KubeManager.write_content_to_file(kube_object)

    assert filename == '/tmp/kubesandbox/12345678-1234-5678-1234-567812345678.yaml'
    assert os.path.exists(filename)
    with open(filename, 'r') as f:
        assert f.read() == kube_object.yaml_content
