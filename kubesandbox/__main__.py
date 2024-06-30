from __future__ import annotations

import logging
import sys
import time
import traceback
from os import system, name

from pydantic import TypeAdapter

from kubesandbox import config
from kubesandbox.helm.helm_manager import HelmManager
from kubesandbox.helm.model import HelmChart
from kubesandbox.k3d.manager import K3dManager
from kubesandbox.kubeclient.kubectl_manager import KubeManager
from kubesandbox.kubeclient.model import KubeObject
from kubesandbox.navigation import InputMenus
from kubesandbox.planner.planner import ExecutionPlanner
from kubesandbox.planner.support import Step, InstallationSource
from kubesandbox.shellclient.base_shell import Shell
from kubesandbox.utilities.system_patcher import Patcher

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
        ks_chart = adapter.validate_python(config.deployment_config['kubeyaml']['clusterManagers']['kubeSphere'])
        return kube_manager.generate_kubectl_apply_step(ks_chart)
    except:
        logger.error(traceback.format_exc())
        return None


def get_rancher() -> Step | None:
    try:
        rancher_chart = HelmChart.model_validate(config.deployment_config['helm']['clusterManagers']['rancher'])
        return helm_manager.generate_chart_installation_step(rancher_chart)
    except:
        logger.error(traceback.format_exc())
        return None


def prepare_management_tool(tool: str = None) -> Step | None:
    if tool == 'rancher':
        logger.info('Selected Rancher for cluster management.')
        return get_rancher()
    elif tool == 'kubesphere':
        logger.info('Selected KubeSphere for cluster management.')
        return get_kubesphere()
    else:
        logger.info('No cluster management tool selected.')
        return None


def process_build():
    logger.debug(f'Processing build config {config.storage.inputs.model_dump_json(indent=4)}')
    build_steps: list[Step] = []
    inputs = config.storage.inputs

    if inputs.registry:
        build_steps.append(
            K3dManager.prepare_registry(registry='reg:41953')
        )

    build_steps.append(
        K3dManager.prepare_cluster(
            cluster_name=inputs.cluster_name,
            agents=inputs.agents,
            loadbalancer=inputs.loadbalancer,
            nodeports=inputs.nodeports,
            use_default_ingress=(inputs.ingress == 'traefik')
        )
    )

    if inputs.ingress != 'traefik':
        ingress_installation = prepare_ingress(inputs.ingress)

        if ingress_installation:
            ingress_installation.optional = True
            build_steps.append(ingress_installation)

    management_tool = prepare_management_tool(inputs.management_tool)

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
    InputMenus.get_build_description()
    process_build()


def default_build(management_tool: str = None):
    if management_tool:
        config.storage.inputs.management_tool = management_tool
    process_build()


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
            default_build('rancher')
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
