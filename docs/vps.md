# VPS sizing

Wisp MCP itself is small. The VPS only needs to keep Python and, optionally, a private tunnel client running. The game server can remain at the Wisp hosting provider.

A current low-cost Linux VPS is enough for Wisp MCP plus a few lightweight services. As of 2026-08-15, OVHcloud France lists:

| Plan | vCPU | RAM | NVMe | Starting price excluding tax | Good fit |
| --- | ---: | ---: | ---: | ---: | --- |
| VPS-1 | 2 | 4 GB | 40 GB | 3.81 EUR/month | Wisp MCP, tunnel, small sites |
| VPS-2 | 4 | 8 GB | 75 GB | 7.21 EUR/month | several sites, small databases, light CI |
| VPS-3 | 6 | 12 GB | 100 GB | 10.40 EUR/month | heavier builds and multiple services |
| VPS-4 | 8 | 24 GB | 200 GB | 19.96 EUR/month | larger mixed workloads |

Pricing and specifications change. Check the current provider page before buying:

https://www.ovhcloud.com/fr/vps/configurator/

There is no affiliate link in this project.

For Wisp MCP alone, start small. Upgrade only when other services actually need more CPU, memory, or storage.
