# PCPartPicker Residential Egress (feature-003, story-5)

PCPartPicker is a **benchmark-only**, **OFF-by-default** reference source. Its
rows NEVER enter the scoring / dedup / notification pipeline
(`PcPartPickerAdapter.search()` always returns `[]`). It exists solely to refresh
a "vs new-retail" reference price (`benchmark_median` + `vs_retail_delta`) for the
~11 mapped catalog items (see `docs/PCPP_MAPPING.md`).

## Why residential egress (NOT a datacenter IP)

PCPartPicker is behind Cloudflare and its ToS forbids automated scraping. Requests
from **datacenter IPs** (e.g. a cloud/VPS egress in the `104.223.27.177`-class
ranges) get challenged/`403`-blocked almost immediately. To fetch a public product
page politely and at very low volume, requests must leave from a **residential**
IP via a Tailscale exit node on a home connection.

We therefore gate PCPartPicker behind TWO flags — it runs only when BOTH are set:

| Flag | Default | Meaning |
|------|---------|---------|
| `ENABLE_PCPARTPICKER` | `false` | Master switch for the benchmark source. |
| `PCPARTPICKER_USE_RESIDENTIAL_EGRESS` | `false` | Require a residential egress before any call. |
| `PCPARTPICKER_TAILSCALE_EXIT_NODE` | `""` | The Tailscale residential exit-node name/IP; non-empty == "egress configured". |

If `ENABLE_PCPARTPICKER=true` but the egress is not configured,
`refresh_benchmark()` returns `{"skipped": true, "reason": "no_residential_egress"}`
and makes **no live call**.

## Tailscale residential exit-node setup

1. On a machine on your **home/residential** network, install Tailscale and
   advertise it as an exit node:
   ```
   tailscale up --advertise-exit-node
   ```
   Approve the exit node in the Tailscale admin console.
2. On the backend host, join the same tailnet and select that exit node for
   PCPartPicker traffic (either host-wide `tailscale up --exit-node=<node>` or,
   preferably, a transport that binds outbound PCPartPicker requests to the
   residential egress — keep the rest of the app on its normal egress).
3. Set in `.env`:
   ```
   ENABLE_PCPARTPICKER=true
   PCPARTPICKER_USE_RESIDENTIAL_EGRESS=true
   PCPARTPICKER_TAILSCALE_EXIT_NODE=home-residential   # your exit-node name/IP
   ```
4. For real fetches, swap the default `HttpxPcppTransport` for a
   TLS-impersonating fetcher (`curl_cffi`) routed through the residential egress;
   the default `httpx` transport will usually get a Cloudflare `403` and trip the
   circuit breaker. The transport is injectable, so this is a config swap, not a
   code dependency.

## Rate bucket

PCPartPicker has its OWN polite daily bucket — **≤ 200/day**
(`PCPARTPICKER_DAILY_LIMIT`, default 200) — fully separate from eBay's 5,000/day
`RateBudgetManager`. Benchmark refreshes are infrequent (reference prices move
slowly), so real usage is far below this ceiling.

## Circuit breaker

The adapter trips a circuit breaker after
`PCPARTPICKER_CIRCUIT_BREAKER_THRESHOLD` (default 3) **consecutive** transport
errors (e.g. Cloudflare `403`s):

- While **open**, `refresh_benchmark()` returns
  `{"skipped": true, "reason": "circuit_open"}` and makes no call.
- A **single success resets** the consecutive-error count (and effectively closes
  the breaker for the next call).
- The breaker **never raises** — failures degrade to a skipped result so the poll
  loop is never torn down by PCPartPicker.

This keeps a ToS-sensitive, anti-bot-protected source safe to leave wired but
dormant, and cheap to switch on behind the residential egress when desired.
