import os
from typing import Literal, Optional, TypedDict

from ruamel.yaml import YAML

CONFIG_PATH = os.environ.get("MRDM_CONFIG_PATH", "config.yaml")


class DNSParamsT(TypedDict):
    domain: str
    id: str
    key: str


class DNST(TypedDict):
    type: Literal["dnspod"]
    params: DNSParamsT


class NatmapMonitorT(TypedDict):
    enabled: bool
    baseurl: str


class DockerWatcherT(TypedDict):
    enabled: bool
    baseurl: str


class NatmapParamsT(TypedDict):
    internal_port: int


class ManualParamsT(TypedDict):
    record_type: Literal["A", "AAAA", "CNAME"]
    value: str
    port: int


class AddressConfigT(TypedDict):
    type: Literal["natmap", "manual"]
    params: Optional[NatmapParamsT | ManualParamsT]


class ConfigT(TypedDict):
    dns: DNST
    mc_router_baseurl: str
    natmap_monitor: NatmapMonitorT
    docker_watcher: DockerWatcherT
    managed_sub_domain: str
    dns_ttl: int
    addresses: dict[str, AddressConfigT]
    poll_interval: int
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


yaml = YAML(typ="safe")
with open(CONFIG_PATH) as f:
    config: ConfigT = yaml.load(f)
