from __future__ import annotations

import logging
import sys
import time
import traceback
from os import system, name

from pydantic import TypeAdapter
from rich.pretty import pretty_repr

import config
from helm.helm_manager import HelmManager
from helm.model import HelmChart
from k3d.manager import K3dManager
from kubeclient.kubectl_manager import KubeManager
from kubeclient.model import KubeObject
from navigation import InputMenus
from planner.planner import ExecutionPlanner
from planner.support import Step, InstallationSource
from shellclient.base_shell import Shell
from utilities.system_patcher import Patcher

logger = logging.getLogger('App.Main')
logging.getLogger('App.RichDisplay').setLevel(logging.ERROR)

helm_manager = HelmManager()
kube_manager = KubeManager()


def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


def prepare_ingress(ingress: str) -> Step | None:
    try:
        logger.info(f'Selected {ingress} ingress controller.')
        ingress_chart = HelmChart.model_validate(config.deployment_config['helm']['ingressControllers'][ingress])
        return helm_manager.generate_chart_installation_step(ingress_chart)
    except:
        logger.error(traceback.format_exc())
        return None


def get_kubesphere():
    try:
        logger.info('Selected KubeSphere for cluster management.')
        adapter = TypeAdapter(list[KubeObject])
        ks_chart = adapter.validate_python(config.deployment_config['kubeyaml']['clusterManagers']['KubeSphere'])
        return kube_manager.generate_kubectl_apply_step(ks_chart)
    except:
        logger.error(traceback.format_exc())
        return None


def get_rancher() -> Step | None:
    try:
        logger.info('Selected Rancher for cluster management.')
        rancher_chart = HelmChart.model_validate(config.deployment_config['helm']['clusterManagers']['Rancher'])
        return helm_manager.generate_chart_installation_step(rancher_chart)
    except:
        logger.error(traceback.format_exc())
        return None


def prepare_management_tool(tool: str = None) -> Step | None:
    if tool == 'Rancher':
        return get_rancher()
    elif tool == 'Kubesphere':
        return get_kubesphere()
    else:
        return None


def process_build_description(build_description: dict):
    build_steps: list[Step] = []

    if build_description['registry']:
        build_steps.append(
            K3dManager.prepare_registry(registry='reg:41953')
        )

    if f"{build_description['loadbalancer']}".startswith('Direct'):
        loadbalancer = (80, 443)
    elif f"{build_description['loadbalancer']}".startswith('Indirect'):
        loadbalancer = (8080, 4433)
    else:
        loadbalancer = None

    build_steps.append(
        K3dManager.prepare_cluster(
            cluster_name='sandbox',
            agents=int(build_description['agents']),
            loadbalancer=loadbalancer,
            nodeports=int(build_description['nodeports']),
            use_default_ingress=(build_description['ingress'] == 'Traefik')
        )
    )

    if build_description['ingress'] != 'Traefik':
        ingress_installation = prepare_ingress(build_description['ingress'])

        if ingress_installation:
            ingress_installation.optional = True
            build_steps.append(ingress_installation)

    management_tool = prepare_management_tool(build_description['management'])

    if management_tool:
        build_steps.append(management_tool)

    adapter = TypeAdapter(dict[str, InstallationSource])

    plan = ExecutionPlanner(
        steps=build_steps,
        installation_sources=adapter.validate_json(config.installer_config)
    )

    plan.execute()


def build_menu():
    logger.info('Getting build description')
    build_description = InputMenus.get_build_description()
    logger.debug(pretty_repr(build_description))
    process_build_description(build_description)


def default_build(management_tool: str = None):
    build = config.deployment_config['builds']['default_build']
    if management_tool:
        build['management'] = management_tool

    process_build_description(build)


def main():
    clear()
    logger.info('Starting App')
    choice = InputMenus.get_main_menu()

    clear()
    try:
        if choice == 'recreate':
            raise NotImplementedError('Recreate cluster is not yet implemented')
        elif choice == 'build_light':
            default_build()
        elif choice == 'build_heavy':
            default_build('Rancher')
        elif choice == 'basic':
            build_menu()
        elif choice == 'advanced':
            raise NotImplementedError('Advanced configuration is not yet implemented')
        elif choice == 'patch_docker':
            Patcher.fix_rootless_docker()
        elif choice == 'delete':
            output = Shell.execute_command(
                'k3d cluster rm sandbox'.split()
            )
            print(f'{output.stdout}{output.stderr}')
        elif choice == 'exit':
            sys.exit(0)

        time.sleep(3)
        # clear()
        config.chores.cleanup()
    except Exception as e:
        config.chores.should_dump_output = False
        config.chores.should_generate_report = False
        config.chores.cleanup()
        print(e)


if __name__ == "__main__":
    main()
