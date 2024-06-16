import os
from copy import deepcopy
from unittest.mock import patch, MagicMock

import pytest
import yaml

from kubesandbox import config
from kubesandbox.k3d.manager import K3dManager, ClusterConfig
from kubesandbox.planner.support import Step, DisplayMessages
from kubesandbox.storage import Resource

default_cluster_config = {
    'apiVersion': 'k3d.io/v1alpha4',
    'kind': 'Simple',
    'metadata': {'name': 'sandbox'},
    'servers': 1,
    'agents': 0,
    'subnet': 'auto'
}


@pytest.fixture
def mock_time():
    with patch('kubesandbox.k3d.manager.time.time', return_value=1678886400):
        yield


@pytest.fixture
def clean_up():
    yield
    for filename in ['k3d-config-1678886400.yaml']:
        if os.path.exists(filename):
            os.remove(filename)


def test_write_cluster_config_basic(mock_time, clean_up):
    cluster_config = ClusterConfig.model_validate({
        'apiVersion': 'k3d.io/v1alpha4',
        'kind': 'Simple',
        'metadata': {'name': 'sandbox'},
        'agents': 2,
        'ports': [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ],
        'registries': {'use': ['k3d-reg:41953']},
        'servers': 1,
        'subnet': 'auto',
        'options': {
            'k3s': {
                'extraArgs': [
                    {
                        'arg': '--disable=traefik',
                        'nodeFilters': ['server:*']
                    }
                ]
            }
        }
    })

    filename = K3dManager.write_cluster_config(cluster_config)

    assert filename == os.path.abspath('k3d-config-1678886400.yaml')

    with open(filename, 'r') as f:
        data = yaml.safe_load(f)

    expected_data = deepcopy(default_cluster_config)

    expected_data.update(
        {
            'metadata': {'name': 'sandbox'},
            'agents': 2,
            'ports': [
                {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
                {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
            ],
            'registries': {'use': ['k3d-reg:41953']},
            'options': {'k3s': {'extraArgs': [{'arg': '--disable=traefik', 'nodeFilters': ['server:*']}]}}
        })

    assert data == expected_data

    assert len(config.storage.resources) == 1
    assert config.storage.resources[0] == Resource(
        name='K3D Config',
        path='k3d-config-1678886400.yaml',
        type='YAML file',
        details='File containing the configuration for recreating the current K3D cluster. This cluster will '
                'not contain the installed tools or packages.',
        reference='https://k3d.io/v5.6.3/usage/configfile/'
    )


def test_write_cluster_config_no_options(mock_time, clean_up):
    cluster_config = ClusterConfig.model_validate({
        'metadata': {'name': 'sandbox'},
        'agents': 2,
        'ports': [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ],
        'registries': {'use': ['k3d-reg:41953']}
    })

    filename = K3dManager.write_cluster_config(cluster_config)

    assert filename == os.path.abspath('k3d-config-1678886400.yaml')

    with open(filename, 'r') as f:
        data = yaml.safe_load(f)

    expected_data = deepcopy(default_cluster_config)

    expected_data.update({
        'metadata': {'name': 'sandbox'},
        'agents': 2,
        'ports': [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ],
        'registries': {'use': ['k3d-reg:41953']}
    })

    assert data == expected_data


def test_write_cluster_config_no_registries(mock_time, clean_up):
    cluster_config = ClusterConfig.model_validate({
        'metadata': {
            'name': 'sandbox'
        },
        'agents': 2,
        'ports': [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ],
        'options': {
            'k3s': {
                'extraArgs': [
                    {
                        'arg': '--disable=traefik',
                        'nodeFilters': ['server:*']
                    }
                ]
            }
        }
    })

    filename = K3dManager.write_cluster_config(cluster_config)

    assert filename == os.path.abspath('k3d-config-1678886400.yaml')

    with open(filename, 'r') as f:
        data = yaml.safe_load(f)

    expected_data = deepcopy(default_cluster_config)

    expected_data.update({
        'metadata': {'name': 'sandbox'},
        'agents': 2,
        'ports': [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ],
        'options': {'k3s': {'extraArgs': [{'arg': '--disable=traefik', 'nodeFilters': ['server:*']}]}}
    })

    assert data == expected_data


def test_write_cluster_config_no_agents(mock_time, clean_up):
    cluster_config = ClusterConfig.model_validate(
        {
            'metadata': {'name': 'sandbox'},
            'ports': [
                {
                    'port': '8080:80',
                    'nodeFilters':
                        ['loadbalancer']
                },
                {
                    'port': '8443:443',
                    'nodeFilters': ['loadbalancer']
                }
            ],
            'registries': {
                'use': ['k3d-reg:41953']
            },
            'options': {
                'k3s': {
                    'extraArgs': [
                        {
                            'arg': '--disable=traefik',
                            'nodeFilters': ['server:*']
                        }
                    ]
                }
            }
        }
    )

    filename = K3dManager.write_cluster_config(cluster_config)

    assert filename == os.path.abspath('k3d-config-1678886400.yaml')

    with open(filename, 'r') as f:
        data = yaml.safe_load(f)

    expected_data = deepcopy(default_cluster_config)

    expected_data.update({
        'metadata': {'name': 'sandbox'},
        'ports': [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ],
        'registries': {'use': ['k3d-reg:41953']},
        'options': {'k3s': {'extraArgs': [{'arg': '--disable=traefik', 'nodeFilters': ['server:*']}]}}
    })

    assert data == expected_data


@pytest.fixture
def mock_config():
    config.node_port_base = 3000
    config.run_in_user_namespace = False
    config.storage = MagicMock()
    config.storage.resources = []


@pytest.mark.parametrize(
    "loadbalancer, expected_config",
    [
        (None, []),
        ((8080, 8443), [
            {'port': '8080:80', 'nodeFilters': ['loadbalancer']},
            {'port': '8443:443', 'nodeFilters': ['loadbalancer']}
        ])
    ]
)
def test_get_loadbalancer_config(mock_config, loadbalancer, expected_config):
    assert K3dManager.get_loadbalancer_config(loadbalancer) == expected_config


@pytest.mark.parametrize(
    "nodeports, expected_config",
    [
        (0, []),
        (2, [
            {'port': '30000', 'nodeFilters': ['server:0']},
            {'port': '30001', 'nodeFilters': ['server:0']}
        ])
    ]
)
def test_get_nodeport_config(mock_config, nodeports, expected_config):
    assert K3dManager.get_nodeport_config(nodeports) == expected_config


@pytest.mark.parametrize(
    "arg, node_filters, expected_config",
    [
        ('--disable=traefik', ['server:*'], {'arg': '--disable=traefik', 'nodeFilters': ['server:*']}),
        ('--kubelet-arg=feature-gates=KubeletInUserNamespace=true', ['server:*', 'agent:*'],
         {'arg': '--kubelet-arg=feature-gates=KubeletInUserNamespace=true', 'nodeFilters': ['server:*', 'agent:*']})
    ]
)
def test_get_options_arg(mock_config, arg, node_filters, expected_config):
    assert K3dManager.get_options_arg(arg, node_filters) == expected_config


@pytest.mark.parametrize(
    "use_default_ingress, expected_config",
    [
        (True, None),
        (False, {'extraArgs': [{'arg': '--disable=traefik', 'nodeFilters': ['server:*']}]})
    ]
)
def test_get_k3s_config(mock_config, use_default_ingress, expected_config):
    assert K3dManager.get_k3s_config(use_default_ingress) == expected_config


@pytest.mark.parametrize(
    "use_default_ingress, run_in_user_namespace, expected_config",
    [
        (True, False, None),
        (False, False, {'extraArgs': [{'arg': '--disable=traefik', 'nodeFilters': ['server:*']}]}),
        (True, True, {'extraArgs': [
            {'arg': '--kubelet-arg=feature-gates=KubeletInUserNamespace=true', 'nodeFilters': ['server:*', 'agent:*']},
            {'arg': '--kube-controller-manager-arg=feature-gates=KubeletInUserNamespace=true',
             'nodeFilters': ['server:*', 'agent:*']},
            {'arg': '--kube-apiserver-arg=feature-gates=KubeletInUserNamespace=true',
             'nodeFilters': ['server:*', 'agent:*']}
        ]})
    ]
)
def test_get_k3s_config_with_user_namespace(mock_config, use_default_ingress, run_in_user_namespace, expected_config):
    config.run_in_user_namespace = run_in_user_namespace
    assert K3dManager.get_k3s_config(use_default_ingress) == expected_config


@patch('kubesandbox.k3d.manager.K3dManager.write_cluster_config')
def test_prepare_cluster(mock_write_cluster_config, mock_config):
    mock_write_cluster_config.return_value = 'k3d-config.yaml'
    cluster_name = 'my-cluster'
    agents = 2
    registry = 'my-registry:5000'
    loadbalancer = (8080, 8443)
    nodeports = 3
    use_default_ingress = False

    expected_step = Step(
        name='Create cluster',
        dependencies=['k3d'],
        optional=False,
        command='k3d',
        args=['cluster', 'create', '--config', 'k3d-config.yaml'],
        display_messages=DisplayMessages(
            ongoing_message='Creating cluster',
            success_message='Cluster created successfully',
            failure_message='Cluster creation failed. If you are using rootless docker, run the '
                            '"Patch permissions for rootless docker" option from the menu then try again.'
        ),
        on_success=Step(
            name='merge_kube_config',
            dependencies=['k3d'],
            optional=False,
            quoted_command='k3d kubeconfig merge my-cluster --kubeconfig-merge-default &> /dev/null',
            display_messages=DisplayMessages(
                ongoing_message='Updating kubeconfig',
                success_message='Kubeconfig updated',
                failure_message='Kubeconfig update failed'
            )
        )
    )

    step = K3dManager.prepare_cluster(
        cluster_name=cluster_name,
        agents=agents,
        registry=registry,
        loadbalancer=loadbalancer,
        nodeports=nodeports,
        use_default_ingress=use_default_ingress
    )

    assert step == expected_step
    mock_write_cluster_config.assert_called_once()


@patch('kubesandbox.k3d.manager.K3dManager.write_cluster_config')
def test_prepare_cluster_no_agents(mock_write_cluster_config, mock_config):
    mock_write_cluster_config.return_value = 'k3d-config.yaml'
    cluster_name = 'my-cluster'
    agents = 0
    registry = 'my-registry:5000'
    loadbalancer = (8080, 8443)
    nodeports = 3
    use_default_ingress = False

    expected_step = Step(
        name='Create cluster',
        dependencies=['k3d'],
        optional=False,
        command='k3d',
        args=['cluster', 'create', '--config', 'k3d-config.yaml'],
        display_messages=DisplayMessages(
            ongoing_message='Creating cluster',
            success_message='Cluster created successfully',
            failure_message='Cluster creation failed. If you are using rootless docker, run the '
                            '"Patch permissions for rootless docker" option from the menu then try again.'
        ),
        on_success=Step(
            name='merge_kube_config',
            dependencies=['k3d'],
            optional=False,
            quoted_command='k3d kubeconfig merge my-cluster --kubeconfig-merge-default &> /dev/null',
            display_messages=DisplayMessages(
                ongoing_message='Updating kubeconfig',
                success_message='Kubeconfig updated',
                failure_message='Kubeconfig update failed'
            )
        )
    )

    step = K3dManager.prepare_cluster(
        cluster_name=cluster_name,
        agents=agents,
        registry=registry,
        loadbalancer=loadbalancer,
        nodeports=nodeports,
        use_default_ingress=use_default_ingress
    )

    assert step == expected_step
    mock_write_cluster_config.assert_called_once()


@pytest.mark.parametrize(
    "registry, expected_step",
    [
        ('my-registry:5000', Step(
            name='check_registry_exists',
            dependencies=['docker', 'k3d', 'grep', 'kubectl'],
            quoted_command='[ $(k3d registry get k3d-my-registry --no-headers 2> /dev/null | grep -ic \'^k3d-my-registry \\+registry \\+running\') -eq 1 ]',
            optional=True,
            display_messages=DisplayMessages(
                ongoing_message='Checking if the registry already exists',
                success_message='Registry exists',
                failure_message='Registry does not exist'
            ),
            on_failure=Step(
                name='createRegistry',
                dependencies=['docker', 'k3d'],
                optional=False,
                command='k3d',
                args=['registry', 'create', '-p', '5000', 'my-registry'],
                display_messages=DisplayMessages(
                    ongoing_message='Creating registry',
                    success_message='Registry created',
                    failure_message='Registry creation failed'
                )
            )
        ))
    ]
)
def test_prepare_registry(mock_config, registry, expected_step):
    step = K3dManager.prepare_registry(registry)
    assert step == expected_step
