from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, Annotated

from pydantic import BaseModel, Field, StringConstraints, ConfigDict
from typing_extensions import Literal

name_pattern = (r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{'
                r'0,61}[A-Za-z0-9])$')
node_filter_example = ['loadbalancer', 'server:*', 'server:0', 'agent:1', 'all']


class Metadata(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Annotated[str, StringConstraints(pattern=name_pattern)] | None = None
    """
    Name of the cluster (must be a valid hostname and will be prefixed with 'k3d-'). Example: 'mycluster'.
    """


class KubeAPI(BaseModel):
    model_config = ConfigDict(extra='forbid')

    host: Annotated[str, StringConstraints(pattern=name_pattern)] | None = None
    hostIP: IPv4Address | None = Field(None, examples=['0.0.0.0', '192.168.178.55'])
    hostPort: str | None = Field(None, examples=['6443'])


class Loadbalancer(BaseModel):
    model_config = ConfigDict(extra='forbid')

    configOverrides: list | None = Field(
        None,
        examples=[
            'settings.workerConnections=2048',
            'settings.defaultProxyTimeout=900',
        ],
    )


class K3dConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    wait: bool | None = True
    timeout: Any | None = Field(None, examples=['60s', '1m', '1m30s'])
    disableLoadbalancer: bool | None = False
    disableImageVolume: bool | None = False
    disableRollback: bool | None = False
    loadbalancer: Loadbalancer | None = None


class Kubeconfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    updateDefaultKubeconfig: bool | None = True
    switchCurrentContext: bool | None = True


class Proxy(BaseModel):
    model_config = ConfigDict(extra='forbid')

    remoteURL: str | None = Field(None, examples=['https://registry-1.docker.io'])
    username: str | None = None
    password: str | None = None


class Create(BaseModel):
    """
    Create a new container image registry alongside the cluster.
    """

    model_config = ConfigDict(extra='forbid')

    name: str | None = Field(None, examples=['myregistry', 'registry.localhost'])
    host: str | None = Field('0.0.0.0', examples=['0.0.0.0', 'localhost', '127.0.0.1'])
    hostPort: str | None = Field('random', examples=['5000', '2345'])
    image: str | None = Field(
        'docker.io/library/registry:2', examples=['myregistry/registry:2']
    )
    proxy: Proxy | None = None
    volumes: list[str] | None = Field(
        None, examples=['/tmp/registry:/var/lib/registry']
    )


class Registries(BaseModel):
    create: Create | None = None
    """
    Create a new container image registry alongside the cluster.
    """
    use: list[str] | None = Field(None, examples=['otherregistry:5000'])
    """
    Connect another container image registry to the cluster.
    """
    config: str | None = None
    """
    Reference a K3s registry configuration file or at it's contents here.
    """
    additionalProperties: Any | None = None


class HostAliase(BaseModel):
    ip: str | None = None
    hostnames: list[str] | None = None


class Volume(BaseModel):
    model_config = ConfigDict(extra='forbid')

    volume: str | None = None
    nodeFilters: list[str] | None = Field(
        None, examples=node_filter_example
    )


class Port(BaseModel):
    model_config = ConfigDict(extra='forbid')

    port: str | None = None
    nodeFilters: list[str] | None = Field(
        None, examples=node_filter_example
    )


class ExtraArg(BaseModel):
    model_config = ConfigDict(extra='forbid')

    arg: str | None = Field(None, examples=['--tls-san=127.0.0.1', '--disable=traefik'])
    nodeFilters: list[str] | None = Field(
        None, examples=node_filter_example
    )


class NodeLabel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    label: str | None = None
    nodeFilters: list[str] | None = Field(
        None, examples=node_filter_example
    )


class K3sConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    extraArgs: list[ExtraArg] | None = None
    nodeLabels: list[NodeLabel] | None = None


class Label(NodeLabel):
    pass


class Runtime(BaseModel):
    gpuRequest: str | None = None
    serversMemory: str | None = None
    agentsMemory: str | None = None
    hostPidMode: bool | None = False
    labels: list[Label] | None = None


class Options(BaseModel):
    model_config = ConfigDict(extra='forbid')

    k3d: K3dConfig | None = None
    k3s: K3sConfig | None = None
    kubeconfig: Kubeconfig | None = None
    runtime: Runtime | None = None


class EnvItem(BaseModel):
    model_config = ConfigDict(extra='forbid')

    envVar: str | None = None
    nodeFilters: list[str] | None = Field(
        None, examples=['loadbalancer', 'server:*', 'server:0', 'agent:1', 'all']
    )


class ClusterConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    apiVersion: Literal['k3d.io/v1alpha4'] | None = 'k3d.io/v1alpha4'
    kind: Literal['Simple'] | None = 'Simple'
    metadata: Metadata | None = Metadata(name='sandbox')
    servers: Annotated[int, Field(strict=True, ge=1)] | None = 1
    agents: Annotated[int, Field(strict=True, gt=0)] | None = 0
    kubeAPI: KubeAPI | None = None
    image: str | None = Field(None, examples=['rancher/k3s:latest'])
    network: str | None = None
    subnet: str | None = Field('auto', examples=['172.28.0.0/16', '192.162.0.0/16'])
    token: str | None = None
    volumes: list[Volume] | None = None
    ports: list[Port] | None = None
    options: Options | None = None
    env: list[EnvItem] | None = None
    registries: Registries | None = None
    hostAliases: list[HostAliase] | None = None
    """
    Additional IP to multiple hostnames mappings
    """
