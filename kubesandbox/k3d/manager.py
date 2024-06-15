from __future__ import annotations

import json
import logging
import os
import shlex
import time
from typing import Any

import yaml

from kubesandbox import config
from kubesandbox.k3d.model import ClusterConfig
from kubesandbox.planner.support import Step, DisplayMessages
from kubesandbox.storage import Resource

logger = logging.getLogger('App.K3dManager')


class K3dManager:
    """
    A class to manage K3D clusters.
    """

    @classmethod
    def get_loadbalancer_config(cls, loadbalancer: tuple[int, int] | None) -> list[dict]:
        """
        Generates a list of dictionaries representing loadbalancer configuration.

        Args:
            loadbalancer: A tuple containing the port mappings for the loadbalancer,
                or None if no loadbalancer is required.

        Returns:
            A list of dictionaries containing loadbalancer port mappings and node filters.
        """
        logger.info(f'Generating loadbalancer config for mapping {loadbalancer}')
        if loadbalancer:
            return [
                {
                    'port': f'{loadbalancer[0]}:80',
                    'nodeFilters': ['loadbalancer']
                },
                {
                    'port': f'{loadbalancer[1]}:443',
                    'nodeFilters': ['loadbalancer']
                }
            ]
        else:
            return []

    @classmethod
    def get_nodeport_config(cls, nodeports: int):
        """
        Generates a list of dictionaries representing nodeport configuration.

        Args:
            nodeports: The number of nodeports to configure.

        Returns:
            A list of dictionaries containing nodeport mappings and node filters.
        """
        logger.info(f'Generating nodeport config for {nodeports} ports.')
        return [
            {
                'port': f'{config.node_port_base}{i}',
                'nodeFilters': ['server:0']
            }
            for i in range(nodeports)
        ]

    @classmethod
    def get_options_arg(cls, arg: str, node_filters: list) -> dict:
        return {
            'arg': arg,
            'nodeFilters': node_filters
        }

    @classmethod
    def get_k3s_config(cls, use_default_ingress: bool) -> dict[str, list[Any]] | None:
        args = []

        servers_only = ['server:*']
        servers_and_agents = ['server:*', 'agent:*']

        if not use_default_ingress:
            args.append(cls.get_options_arg('--disable=traefik', servers_only))

        if config.run_in_user_namespace:
            args.extend([
                cls.get_options_arg('--kubelet-arg=feature-gates=KubeletInUserNamespace=true', servers_and_agents),
                cls.get_options_arg('--kube-controller-manager-arg=feature-gates=KubeletInUserNamespace=true',
                                    servers_and_agents),
                cls.get_options_arg('--kube-apiserver-arg=feature-gates=KubeletInUserNamespace=true',
                                    servers_and_agents)
            ])

        if args:
            return {'extraArgs': args}
        else:
            return None

    @classmethod
    def prepare_cluster(
            cls,
            cluster_name: str = 'sandbox',
            agents: int = 0,
            registry: str = 'reg:41953',
            loadbalancer: tuple[int, int] | None = None,
            nodeports: int = 0,
            use_default_ingress: bool = True
    ) -> Step:
        """
        Generates a Step object representing the creation of a K3D cluster.

        Args:
            cluster_name: The name of the cluster to create.
            agents: The number of agent nodes in the cluster.
            registry: The name and port of the registry to use for the cluster.
            loadbalancer: A tuple containing the port mappings for the loadbalancer,
                or None if no loadbalancer is required.
            nodeports: The number of nodeports to configure.
            use_default_ingress: Whether to use the default ingress controller.

        Returns:
            A Step object containing the command and parameters for creating the cluster.
        """
        logger.info(f'Generating cluster config for cluster "{cluster_name}"')
        cluster_config_dict = {
            'metadata': {
                'name': cluster_name
            }
        }

        if agents:
            logger.info(f'Adding {agents} agents to the cluster config')
            cluster_config_dict['agents'] = agents

        cluster_config_dict['ports'] = cls.get_loadbalancer_config(loadbalancer)

        if nodeports:
            cluster_config_dict['ports'] += (cls.get_nodeport_config(nodeports))

        if registry:
            logger.info(f'Adding registry "{registry}" to the cluster config')
            cluster_config_dict['registries'] = {}
            cluster_config_dict['registries']['use'] = [f'k3d-{registry}']

        k3s_config = cls.get_k3s_config(use_default_ingress)

        if k3s_config:
            cluster_config_dict['options'] = {
                'k3s': k3s_config
            }

        logger.debug(f'Validating generated model:\n {cluster_config_dict}')

        cluster_config = ClusterConfig.model_validate_json(json.dumps(cluster_config_dict))

        config_filename = cls.write_cluster_config(cluster_config)

        return Step(
            name='Create cluster',
            dependencies=['k3d'],
            optional=False,
            command='k3d',
            args=['cluster', 'create', '--config', config_filename],
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
                quoted_command=f'k3d kubeconfig merge {shlex.quote(cluster_name)} --kubeconfig-merge-default &> /dev/null',
                display_messages=DisplayMessages(
                    ongoing_message='Updating kubeconfig',
                    success_message='Kubeconfig updated',
                    failure_message='Kubeconfig update failed'
                )
            )
        )

    @staticmethod
    def prepare_registry(registry: str) -> Step:
        """
        Generates a Step object representing the creation of a K3D registry.

        Args:
            registry: The name and port of the registry to create.

        Returns:
            A Step object containing the command and parameters for creating the registry.
        """
        registry_name = registry.split(':')[0]
        registry_port = registry.split(':')[1]

        logger.info(f'Preparing registry "{registry_name}" on port "{registry_port}"')

        return Step(
            name='check_registry_exists',
            dependencies=['docker', 'k3d', 'grep', 'kubectl'],
            quoted_command=f'[ $(k3d registry get k3d-{registry_name} --no-headers 2> /dev/null |'
                           f' grep -ic \'^k3d-{registry_name} \\+registry \\+running\') -eq 1 ]',
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
                args=['registry', 'create', '-p', f'{registry_port}', registry_name],
                display_messages=DisplayMessages(
                    ongoing_message='Creating registry',
                    success_message='Registry created',
                    failure_message='Registry creation failed'
                )
            )
        )

    @classmethod
    def write_cluster_config(cls, cluster_config: ClusterConfig) -> str:
        """
        Writes the cluster configuration to a YAML file.

        Args:
            cluster_config: The ClusterConfig object containing the cluster configuration.

        Returns:
            The filename of the written YAML file.
        """
        epoch_time = int(time.time())
        filename = f'k3d-config-{epoch_time}.yaml'
        absolute_filename = os.path.join(os.getcwd(), filename)

        logger.info(f'Writing cluster config to "{absolute_filename}"')

        with open(filename, 'w+') as file:
            yaml.dump(cluster_config.model_dump(exclude_none=True), file)

        config.storage.resources.append(
            Resource(
                name='K3D Config',
                path=filename,
                type='YAML file',
                details='File containing the configuration for recreating the current K3D cluster. This cluster will '
                        'not contain the installed tools or packages.',
                reference='https://k3d.io/v5.6.3/usage/configfile/'
            )
        )

        return absolute_filename
