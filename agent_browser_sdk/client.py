"""
agent_browser_sdk/client.py
Async + sync HTTP clients for Agent Browser Knowledge Graph API.
Auto-handles x402 payment flow.
"""

import httpx
import asyncio
import os
from typing import Optional, List, Dict, Any
from .models import Venue, Offering, SearchResult, Recommendation, PricingAnalytics


DEFAULT_BASE_URL = "https://medspa-refinery-api-44xz.onrender.com"


class AgentBrowserClient:
    """Sync client for Agent Browser Knowledge Graph API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        mock_payment: bool = True,
        wallet_private_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key  # For Stripe-backed keys (coming)
        self.mock_payment = mock_payment
        self.wallet_private_key = wallet_private_key
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json", "User-Agent": "agent-browser-sdk/1.0"}
        if self.mock_payment:
            h["X-Mock-Payment-Paid"] = "true"
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _handle_402(self, resp: httpx.Response, endpoint: str) -> Dict:
        """Parse 402 challenge, attempt payment, retry."""
        if resp.status_code != 402:
            return resp.json() if resp.content else {}
        spec = resp.headers.get("PAYMENT-REQUIRED")
        if not spec:
            raise Exception(f"402 returned but no PAYMENT-REQUIRED header: {resp.text}")
        import base64, json
        payment_spec = json.loads(base64.b64decode(spec).decode())
        # In real flow: sign USDC tx here. For now, surface error.
        raise PaymentRequired(
            f"x402 payment required: ${payment_spec['price']['amount_usd']} USDC "
            f"to {payment_spec['pay_to']} on {payment_spec['price']['network']}. "
            f"Pass X-Mock-Payment-Paid: true for testing."
        )

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        neighborhood: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price_level: Optional[str] = None,
        limit: int = 10
    ) -> SearchResult:
        """Multi-category intent search."""
        params = {"limit": limit}
        if query: params["query"] = query
        if category: params["category"] = category
        if neighborhood: params["neighborhood"] = neighborhood
        if min_rating is not None: params["min_rating"] = min_rating
        if max_price_level: params["max_price_level"] = max_price_level

        resp = self._client.get(
            f"{self.base_url}/api/v1/search",
            params=params,
            headers=self._headers()
        )
        data = self._handle_402(resp, "search")
        return SearchResult(**data)

    def recommend(
        self,
        category: str,
        preferred_area: Optional[str] = None,
        required_features: Optional[List[str]] = None,
        max_price_level: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Get ranked recommendations for an intent."""
        payload = {"category": category, "limit": limit}
        if preferred_area: payload["preferred_area"] = preferred_area
        if required_features: payload["required_features"] = required_features
        if max_price_level: payload["max_price_level"] = max_price_level
        if min_rating is not None: payload["min_rating"] = min_rating

        resp = self._client.post(
            f"{self.base_url}/api/v1/recommend",
            json=payload,
            headers=self._headers()
        )
        return self._handle_402(resp, "recommend")

    def get_venue(self, venue_id: int) -> Dict[str, Any]:
        """Get detailed venue info."""
        resp = self._client.get(
            f"{self.base_url}/api/v1/venues/{venue_id}",
            headers=self._headers()
        )
        return self._handle_402(resp, f"venue:{venue_id}")

    def list_venues(
        self,
        category: Optional[str] = None,
        neighborhood: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List venues with filters."""
        params = {"limit": limit}
        if category: params["category"] = category
        if neighborhood: params["neighborhood"] = neighborhood
        if min_rating is not None: params["min_rating"] = min_rating

        resp = self._client.get(
            f"{self.base_url}/api/v1/venues",
            params=params,
            headers=self._headers()
        )
        return self._handle_402(resp, "venues")

    def pricing_analytics(
        self,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get category-specific pricing analytics."""
        params = {}
        if category: params["category"] = category
        resp = self._client.get(
            f"{self.base_url}/api/v1/analytics/pricing-summary",
            params=params,
            headers=self._headers()
        )
        return self._handle_402(resp, "pricing-summary")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AsyncAgentBrowserClient:
    """Async client for Agent Browser Knowledge Graph API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        mock_payment: bool = True,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.mock_payment = mock_payment
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json", "User-Agent": "agent-browser-sdk/1.0"}
        if self.mock_payment:
            h["X-Mock-Payment-Paid"] = "true"
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        neighborhood: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price_level: Optional[str] = None,
        limit: int = 10
    ) -> SearchResult:
        params = {"limit": limit}
        if query: params["query"] = query
        if category: params["category"] = category
        if neighborhood: params["neighborhood"] = neighborhood
        if min_rating is not None: params["min_rating"] = min_rating
        if max_price_level: params["max_price_level"] = max_price_level

        resp = await self._client.get(
            f"{self.base_url}/api/v1/search",
            params=params,
            headers=self._headers()
        )
        if resp.status_code == 402:
            raise PaymentRequired("x402 payment required. Use mock_payment=True for testing.")
        return SearchResult(**resp.json())

    async def recommend(
        self,
        category: str,
        preferred_area: Optional[str] = None,
        required_features: Optional[List[str]] = None,
        max_price_level: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        payload = {"category": category, "limit": limit}
        if preferred_area: payload["preferred_area"] = preferred_area
        if required_features: payload["required_features"] = required_features
        if max_price_level: payload["max_price_level"] = max_price_level
        if min_rating is not None: payload["min_rating"] = min_rating

        resp = await self._client.post(
            f"{self.base_url}/api/v1/recommend",
            json=payload,
            headers=self._headers()
        )
        if resp.status_code == 402:
            raise PaymentRequired("x402 payment required. Use mock_payment=True for testing.")
        return resp.json()

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


class PaymentRequired(Exception):
    """Raised when x402 payment is required."""
    pass


# LangChain tool wrapper
def create_langchain_tool():
    """Create a LangChain-compatible Tool wrapper."""
    try:
        from langchain.tools import Tool
    except ImportError:
        return None

    def _search_func(query: str) -> str:
        client = AgentBrowserClient(mock_payment=True)
        try:
            result = client.search(query=query, limit=5)
            lines = [f"Found {result.matches_count} matches for: {query}\n"]
            for v in result.data[:5]:
                lines.append(
                    f"- {v.name} ({v.category} in {v.neighborhood}): "
                    f"rating {v.overall_rating}/5, match score {v.agent_match_index}/100. "
                    f"{v.rationale or ''}"
                )
            return "\n".join(lines)
        finally:
            client.close()

    return Tool(
        name="agent_browser_search",
        description=(
            "Search the Agent Browser Knowledge Graph for local venues (cafes, restaurants, "
            "hotels, medspas) across the US. Input: a natural language query like "
            "'wifi cafe in Wynwood' or 'luxury hotel in Miami'. "
            "Returns ranked results with ratings, sentiment tags, and match scores."
        ),
        func=_search_func
    )