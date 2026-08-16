# Agent Browser SDK (Python)

**The Google for AI Agents** — queryable knowledge graph for 190+ venues across cafes, restaurants, hotels, and medspas. Monetized via x402 HTTP 402 micropayments.

## Install

```bash
pip install agent-browser-sdk
```

## Quick Start

```python
from agent_browser_sdk import AgentBrowserClient

with AgentBrowserClient(mock_payment=True) as client:
    # Multi-category intent search
    results = client.search(query="wifi cafe in wynwood", limit=5)
    for venue in results.data:
        print(f"{venue.name} ({venue.agent_match_index}/100): {venue.rationale}")

    # Get recommendations
    recs = client.recommend(
        category="cafe",
        preferred_area="Wynwood",
        required_features=["fast_wifi", "outdoor_seating"],
        max_price_level="$$"
    )
    for r in recs["data"]:
        print(f"Recommend: {r['name']} - {r['_rationale']}")

    # Pricing analytics
    analytics = client.pricing_analytics(category="cafe")
    print(f"Average espresso: ${analytics['data'][0]['avg_price_usd']}")
```

## LangChain Tool

```python
from agent_browser_sdk.client import create_langchain_tool

tool = create_langchain_tool()
# Add to your LangChain agent...
```

## x402 Payment (Real Flow)

For production, set `mock_payment=False` and provide `wallet_private_key`:

```python
client = AgentBrowserClient(
    mock_payment=False,
    wallet_private_key="0x..."  # Base network wallet
)
```

The SDK auto-signs USDC transfers for each request ($0.002 USDC).

## Endpoints

| Method | Endpoint | Cost | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/search` | $0.002 USDC | Multi-category intent search |
| `POST` | `/api/v1/recommend` | $0.005 USDC | Ranked recommendations |
| `GET` | `/api/v1/venues` | $0.002 USDC | List venues |
| `GET` | `/api/v1/venues/{id}` | $0.002 USDC | Venue details |
| `GET` | `/api/v1/analytics/pricing-summary` | $0.002 USDC | Price analytics |

## Live API

- **Base URL:** `https://medspa-refinery-api-44xz.onrender.com`
- **Manifest:** `/llms.json`
- **Docs:** `/docs`
- **Pay-To:** `0x8Ae639d10b23Eb630241d7fD6275255a2e51Ec95` (Base Network)

## License

MIT