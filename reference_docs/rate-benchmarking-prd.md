# PRD: Market rate benchmarking for RFQ quoting

> _Sample reference document for writing-style matching only. Fictional B2B freight context; cost figures are illustrative estimates, not actual vendor pricing._

## Overview
Integrate an ocean and air freight rate intelligence platform into the RFQ workflow so that every quote shared with a client is validated against an independent market benchmark. The goal is to ensure pricing is competitive (not leaving money on the table) and defensible (not quoting below market), with minimal added time to the quoting process.

## Goals
- Benchmark every RFQ against market rates before the quote reaches the client
- Keep the benchmarking step fast enough that it doesn't slow down quote turnaround
- Give the quoting team a clear market position indicator (above, at, or below market?)
- Build a data layer that over time reveals which lanes are consistently strong or weak

## Non-goals
- Replacing human judgment in pricing -- this is decision-support, not auto-pricing
- Surfacing benchmarking data directly to clients (restricted by typical API license terms)
- Air freight benchmarking in Phase 1 (ocean FCL is the priority; air can follow)

---

## The benchmarking use case

### What happens today
The quoting team receives an RFQ, pulls buy rates from carriers and NVOCCs, applies margin, and sends the quote. There is no systematic check of whether the final price is competitive relative to the broader market. Pricing instincts are based on experience, not data.

### What this changes
Before a quote is sent, the system queries the rate intelligence API for the market rate on that origin-destination-container type combination and displays a benchmark comparison. The quoting user sees whether the proposed rate is below, at, or above the market low/average/high -- and can adjust accordingly.

### Speed requirement
RFQ turnaround is time-sensitive. The benchmarking lookup must add no more than **2-3 seconds** to the workflow. Rate intelligence APIs typically respond in under 1 second for port-to-port queries, which fits this constraint.

---

## Approach evaluation: Standard API vs. MCP wrapper

Both approaches use the same underlying rate intelligence REST API and the same platform subscription. The difference is in how the integration is consumed within the platform.

### Option A: Standard API integration

Direct backend integration -- the application server calls the rate intelligence API during the quoting flow.

**How it works:**
- Backend service calls the estimated-rates endpoint with origin port, destination port, container type, and date
- Response returns market low, average, and high rates
- The UI displays the benchmark alongside the proposed quote

**Pros:**
- Deterministic and predictable -- same query always returns same result
- Easy to audit and log every benchmark check
- No additional abstraction layer; fewer moving parts
- Fits naturally into existing application architecture
- Rate limiting and quota management are straightforward to monitor

**Cons:**
- Requires dedicated backend development (API client, error handling, caching, UI integration)
- Each new use case (e.g., adding air freight, adding carrier spread data) requires code changes
- No conversational interface -- quoting team must use the app UI only

**Best for:** Production quoting workflow embedded in the application

### Option B: MCP server wrapping the rate intelligence API

Build a lightweight MCP (Model Context Protocol) server that wraps the API, enabling AI agents and tools to query market rates conversationally.

**How it works:**
- Python or TypeScript MCP server exposes tools like `get_market_rate(origin, destination, container_type)`
- AI agent calls the tool, gets structured rate data back
- Can be used in any MCP-compatible client

**Pros:**
- Enables natural-language rate queries ("What's the market rate for a 40HC from Shanghai to Rotterdam?")
- Extremely fast to build -- 4 to 8 hours for a working MCP server using the official SDK
- Flexible -- adding new tools (carrier spread, capacity, trends) is just adding a new function
- Useful beyond quoting -- sales prep, market research, management reporting
- Can coexist with Option A -- the MCP server can call the same API

**Cons:**
- Adds an abstraction layer between the user and the data
- AI interpretation adds a small amount of unpredictability vs. direct API
- Not suitable as the sole integration for the production quoting UI -- still need Option A for the app
- Requires MCP client setup for each user who wants conversational access
- Newer technology -- less battle-tested in production freight workflows

**Best for:** Ad-hoc analysis, sales preparation, AI-assisted pricing decisions, and internal research

### Recommendation

**Do both, in sequence.** Start with the MCP wrapper (Phase 1) because it's fast to build, immediately useful for the quoting team's ad-hoc needs, and serves as a proof of concept. Then build the standard API integration (Phase 2) to embed benchmarking directly into the production quoting UI.

| Criteria | Standard API | MCP Wrapper |
|----------|-------------|-------------|
| Build time | 2-4 weeks | 4-8 hours |
| Ongoing maintenance | Medium | Low |
| User experience | Structured UI | Conversational |
| Production-readiness | High | Medium |
| Flexibility for new use cases | Low (code changes) | High (add tools) |
| Dependency on AI layer | None | Yes |

---

## Cost evaluation

### Rate intelligence subscription (applies to both approaches)

Rate intelligence platforms do not typically publish pricing. All plans are custom-quoted based on volume, lanes, and features. The figures below are illustrative order-of-magnitude estimates for planning only, not actual vendor quotes.

| Cost component | Illustrative range | Notes |
|----------------|----------------|-------|
| Platform subscription (ocean) | low-to-mid five figures/yr | Varies widely by forwarder size; smaller orgs trend lower |
| API add-on | Included, or a low-five-figure add-on/yr | Depends on call quota |
| Monthly call quota | Defined per plan | Exceeding quota may trigger warnings or temporary suspension |
| Typical ROI claim | Recovered within a tender cycle | Vendors market low-single-digit % freight spend savings |

### MCP wrapper build cost (one-time, Phase 1)

| Cost component | Estimate | Notes |
|----------------|----------|-------|
| Development time | 4-8 hours | Using Python FastMCP or TypeScript SDK |
| Developer cost | $400-$1,200 | At $50-$150/hr depending on in-house vs. contractor |
| Ongoing maintenance | ~2 hrs/month | SDK updates, minor fixes |
| Infrastructure | $0-$20/month | Runs locally via stdio or cheap cloud hosting |
| **Total Year 1** | **$700-$2,000** | Excluding platform subscription |

### Standard API integration build cost (Phase 2)

| Cost component | Estimate | Notes |
|----------------|----------|-------|
| Development time | 40-80 hours | Backend client, caching layer, UI components, testing |
| Developer cost | $4,000-$12,000 | Depending on team rate |
| Ongoing maintenance | ~4-8 hrs/month | Monitoring, quota management, feature additions |
| Infrastructure | $50-$200/month | Caching layer (Redis or similar), monitoring |
| **Total Year 1** | **$5,000-$15,000** | Excluding platform subscription |

### Total cost comparison (Year 1)

| Scenario | Platform sub | Build cost | Relative total |
|----------|-------------|------------|-------|
| MCP only (Phase 1) | five-figure subscription | low (hundreds-low thousands) | subscription + minimal build |
| Standard API only | five-figure subscription | mid (low-five figures) | subscription + moderate build |
| Both (recommended) | five-figure subscription | mid (low-five figures) | subscription + moderate build |

**The key insight:** The platform subscription dominates total cost (roughly 80-90%) regardless of approach. The MCP vs. standard API decision is a build strategy question, not a cost question.

---

## Rate intelligence API: Pros and cons for per-RFQ benchmarking

### Pros

| Advantage | Detail |
|-----------|--------|
| Data depth | Very large dataset of real contract and spot transactions across a broad set of global port pairs |
| Rate granularity | Market low, average, high, plus carrier-level spread |
| Short vs. long-term rates | Distinguishes short-term/spot from long-term/contract rates -- critical for matching the RFQ type |
| Container type coverage | Standard dry, reefer, and high-cube equipment across 20' and 40' sizes |
| Surcharge inclusion | Rates include common surcharges (e.g., BAF, CAF, ETS, canal) -- apples-to-apples comparison |
| API response speed | Sub-second response times for port-to-port queries; fits the fast turnaround requirement |
| Estimated rates | When direct data is thin on a lane, the platform returns modeled estimates |
| Market position scoring | See where the proposed rate sits in the market distribution, not just a single number |

### Cons

| Risk | Detail | Mitigation |
|------|--------|------------|
| No public pricing | Cannot evaluate cost without a sales conversation | Request a demo and quote; push for a pilot/trial period |
| Monthly call quota | High-volume RFQ benchmarking could burn through quota fast | Implement a caching layer -- rates don't change hourly; a 6-12 hour cache per lane is reasonable |
| LCL coverage gap | Strongest on FCL; LCL data is thinner | Continue using NVOCC rates as the LCL benchmark |
| No third-party data sharing | API license prohibits sharing data directly with clients | Use internally only; show clients the quote, not the benchmark source |
| Rate limiting (HTTP 429) | Burst queries during peak quoting hours could hit limits | Queue and throttle API calls; caching reduces this significantly |
| Geo-hierarchy fallback | On thin lanes, may return rates for a broader region instead of exact port pair | Surface actual origin/destination metadata so users know the granularity |
| Aggregated rates only | Market averages, not a specific carrier's bookable rate | By design for benchmarking; not a buy rate substitute |

---

## Caching strategy (critical for per-RFQ use)

Since every RFQ triggers a benchmark lookup, and the quoting team may handle dozens to hundreds of RFQs per day, a caching layer is essential to stay within quota and maintain speed.

| Parameter | Recommendation |
|-----------|---------------|
| Cache key | `{origin_port}:{destination_port}:{container_type}:{rate_type}` |
| Cache TTL | 6-12 hours for spot rates; 24 hours for contract rates |
| Cache store | Redis (if available) or in-memory with persistence |
| Cache hit rate target | 60-80% (many RFQs share common lanes) |
| Quota impact | A 70% cache hit rate on 100 daily RFQs reduces API calls from 100 to 30/day (~900/month vs. 3,000/month) |

---

## Phased rollout

### Phase 1: MCP wrapper (Week 1-2)
- Build MCP server wrapping the estimated-rates and carrier-spread endpoints
- Deploy locally for the quoting team lead as a pilot
- Validate data quality and response speed against real RFQs
- Confirm subscription tier and quota are adequate

### Phase 2: Production API integration (Week 3-6)
- Build backend service with caching layer
- Integrate benchmark display into the quoting UI
- Add market position indicator (below / at / above market)
- Logging and audit trail for every benchmark check

### Phase 3: Analytics and expansion (Week 7+)
- Lane-level analytics: which routes are consistently above/below market?
- Margin optimization suggestions based on market position
- Air freight benchmarking
- Historical trend view per lane

---

## Open questions
- What is the actual daily/monthly RFQ volume? This directly determines the API quota tier needed
- Should the benchmark be mandatory (blocking) before a quote is sent, or advisory (optional)?
- Which team members get access to the MCP wrapper vs. the production UI?
- Should caching happen at the application level, or would a shared cache across the quoting team be more appropriate?
- What is the split between FCL and LCL RFQs? (Determines how much value the platform adds vs. needing a separate LCL benchmark)

---

## Success metrics
- Percentage of RFQs benchmarked before quote is sent to client (target: >90% within 60 days)
- Average time added to quoting workflow by the benchmark step (target: <3 seconds)
- Reduction in quotes that come back as "too high" from clients (directional)
- Number of lanes identified where pricing was significantly above/below market
- API call volume vs. quota utilization (target: stay below 80%)
- Quote win rate trend after benchmarking is live
