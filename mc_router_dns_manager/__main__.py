import asyncio

from .client.docker_watcher_client import DockerWatcherClient
from .client.natmap_monitor_client import NatmapMonitorClient
from .config import config
from .dns.dnspod import DNSPodClient
from .dns.huawei import HuaweiDNSClient
from .dns.mcdns import MCDNS
from .monitorer import Monitorer
from .router.mcrouter import MCRouter
from .router.mcrouter_client import MCRouterClient


async def main():
    match config["dns"]["type"]:
        case "dnspod":
            dns_client = DNSPodClient(
                config["dns"]["params"]["domain"],
                config["dns"]["params"]["id"],
                config["dns"]["params"]["key"],
            )
        case "huawei":
            dns_client = HuaweiDNSClient(
                config["dns"]["params"]["domain"],
                config["dns"]["params"]["ak"],
                config["dns"]["params"]["sk"],
                config["dns"]["params"].get("region"),
            )

    mcdns = MCDNS(dns_client, config["managed_sub_domain"], config["dns_ttl"])
    mcrouter_client = MCRouterClient(config["mc_router_baseurl"])
    mcrouter = MCRouter(
        mcrouter_client,
        dns_client.get_domain(),
        config["managed_sub_domain"],
    )

    docker_watcher = DockerWatcherClient(config["docker_watcher"]["baseurl"])
    if config["natmap_monitor"]["enabled"]:
        natmap_monitor = NatmapMonitorClient(config["natmap_monitor"]["baseurl"])
    else:
        natmap_monitor = None

    monitorer = Monitorer(
        mcdns, mcrouter, docker_watcher, natmap_monitor, config["poll_interval"]
    )

    await monitorer.run()


if __name__ == "__main__":
    asyncio.run(main())
