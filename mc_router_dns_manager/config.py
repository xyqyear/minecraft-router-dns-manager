import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

CONFIG_PATH = os.environ.get("MRDM_CONFIG_PATH", "config.yaml")


class DNSPodParams(BaseModel):
    domain: str
    id: str
    key: str


class DNSPod(BaseModel):
    type: Literal["dnspod"] = "dnspod"
    params: DNSPodParams


class HuaweiParams(BaseModel):
    domain: str
    ak: str
    sk: str
    region: str | None


class Huawei(BaseModel):
    type: Literal["huawei"] = "huawei"
    params: HuaweiParams


class NatmapMonitor(BaseModel):
    enabled: bool
    baseurl: str


class DockerWatcher(BaseModel):
    enabled: bool
    servers_root_path: Path
    poll_interval: int = 1


class NatmapParams(BaseModel):
    internal_port: int


class ManualParams(BaseModel):
    record_type: Literal["A", "AAAA", "CNAME"]
    value: str
    port: int


class NatmapAddressConfig(BaseModel):
    type: Literal["natmap"]
    params: NatmapParams


class ManualAddressConfig(BaseModel):
    type: Literal["manual"]
    params: ManualParams


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        yaml_file=CONFIG_PATH,
    )

    dns: DNSPod | Huawei
    mc_router_baseurl: str
    natmap_monitor: NatmapMonitor
    docker_watcher: DockerWatcher
    managed_sub_domain: str = "mc"
    dns_ttl: int = 600
    addresses: dict[str, NatmapAddressConfig | ManualAddressConfig]
    poll_interval: int = 15
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)


config = Config()  # type: ignore
