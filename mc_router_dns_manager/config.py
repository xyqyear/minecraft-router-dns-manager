import os
from typing import Literal, Optional, TypedDict, cast

from ruamel.yaml import YAML

CONFIG_PATH = os.environ.get("MRDM_CONFIG_PATH", "config.yaml")


class DNSPodParamsT(TypedDict):
    domain: str
    id: str
    key: str


class DNSPodT(TypedDict):
    type: Literal["dnspod"]
    params: DNSPodParamsT


class HuaweiParamsT(TypedDict):
    domain: str
    ak: str
    sk: str
    region: str | None


class HuaweiT(TypedDict):
    type: Literal["huawei"]
    params: HuaweiParamsT


class NatmapMonitorT(TypedDict):
    enabled: bool
    baseurl: str


class DockerWatcherT(TypedDict):
    enabled: bool
    servers_root_path: str


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
    dns: DNSPodT | HuaweiT
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
    _config = yaml.load(f)  # type: ignore
    config = cast(ConfigT, _config)
