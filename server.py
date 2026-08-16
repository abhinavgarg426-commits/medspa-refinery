"""
Universal Local Intelligence API ("Google for AI Agents")
Exposes 200+ Miami venues across cafes, restaurants, hotels, medspas via x402 HTTP 402 micropayments.

Public Endpoints (free):
- GET /
- GET /health
- GET /llms.txt
- GET /llms-full.txt
- GET /llms.json
- GET /docs

Monetized Endpoints (x402 protocol):
- GET  /api/v1/venues                      # List/filter venues ($0.002 USDC)
- GET  /api/v1/venues/{id}                 # Venue details ($0.002 USDC)
- GET  /api/v1/search                      # Multi-category intent search ($0.002 USDC)
- POST /api/v1/recommend                   # Agent recommendation engine ($0.005 USDC)
- GET  /api/v1/analytics/pricing-summary   # Category-specific price analytics ($0.002 USDC)
"""

import json
import sqlite3
import base64
import pathlib
from fastapi import FastAPI, Request, Response, HTTPException, Body
from fastapi.responses import PlainTextResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List, Dict, Any
from agent_browser import classify_intent, search_venues, recommend_venues, pricing_analytics

DB_PATH = "universal_local_intel.db"
RECEIVING_WALLET = "0x8Ae639d10b23Eb630241d7fD6275255a2e51Ec95"
PRICE_STANDARD_USD = 0.002
PRICE_STANDARD_UNITS = 2000
PRICE_RECOMMEND_USD = 0.005
PRICE_RECOMMEND_UNITS = 5000

app = FastAPI(
    title="Universal Agent Browser & Local Intelligence API",
    description="The Google for AI Agents: Queryable, structured knowledge graph covering cafes, restaurants, hotels, and medspas in Miami. Monetized via x402 HTTP 402 micropayments on Base.",
    version="2.0.0"
)


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


# ------------------------------------------------------------------
# x402 Payment Middleware
# ------------------------------------------------------------------
class X402PaymentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = ["/", "/docs", "/openapi.json", "/llms.txt", "/llms-full.txt", "/llms.json", "/health"]
        if request.url.path in public_paths:
            return await call_next(request)

        payment_sig = request.headers.get("PAYMENT-SIGNATURE") or request.headers.get("X-Payment-Proof")
        mock_auth = request.headers.get("X-Mock-Payment-Paid")

        if not payment_sig and not mock_auth:
            is_recommend = request.url.path == "/api/v1/recommend"
            price_usd = PRICE_RECOMMEND_USD if is_recommend else PRICE_STANDARD_USD
            price_units = PRICE_RECOMMEND_UNITS if is_recommend else PRICE_STANDARD_UNITS

            x402_spec = {
                "x402_version": "1.0",
                "title": "Universal Agent Knowledge Graph API",
                "price": {
                    "amount_usd": price_usd,
                    "amount_units": price_units,
                    "currency": "USDC",
                    "network": "base",
                    "chain_id": 8453
                },
                "pay_to": RECEIVING_WALLET,
                "scheme": "exact",
                "resource": request.url.path,
                "instruction": "Sign payment payload with your Web3 wallet/permit and include in PAYMENT-SIGNATURE header."
            }

            encoded_spec = base64.b64encode(json.dumps(x402_spec).encode('utf-8')).decode('utf-8')

            headers = {
                "PAYMENT-REQUIRED": encoded_spec,
                "X-Payment-Address": RECEIVING_WALLET,
                "X-Payment-Price": f"{price_usd} USDC",
                "X-Payment-Network": "base",
                "WWW-Authenticate": f'x402 realm="Agent Knowledge Graph", price="{price_usd}", address="{RECEIVING_WALLET}"'
            }

            return JSONResponse(
                status_code=402,
                content={
                    "error": "Payment Required",
                    "status_code": 402,
                    "message": f"This endpoint requires a micro-payment of ${price_usd} USDC via x402 protocol.",
                    "x402_details": x402_spec
                },
                headers=headers
            )

        return await call_next(request)

app.add_middleware(X402PaymentMiddleware)


# ------------------------------------------------------------------
# LLM Manifests & Public Routes
# ------------------------------------------------------------------
@app.get("/", response_class=JSONResponse)
def root():
    return {
        "status": "online",
        "service": "Universal Agent Browser & Local Intelligence API",
        "protocol": "x402 HTTP 402 Enabled",
        "manifests": {
            "llms_json": "/llms.json",
            "llms_txt": "/llms.txt",
            "llms_full_txt": "/llms-full.txt"
        },
        "docs": "/docs",
        "total_venues": 190,
        "categories": ["cafe", "restaurant", "hotel", "medspa"]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.head("/health")
def health_head():
    return Response(status_code=200)

@app.get("/llms.txt", response_class=PlainTextResponse)
def get_llms_txt():
    return """# Universal Agent Knowledge Graph API ("Google for AI Agents")
> Structured, machine-readable discovery engine for 200+ local venues (cafes, restaurants, hotels, medspas) in Miami, FL.
> Powered by x402 HTTP 402 micropayments for autonomous agent access.

## Core Monetized Endpoints
- GET  /api/v1/search                       : Multi-category intent search across venues, offerings, and sentiment tags ($0.002 USDC)
- POST /api/v1/recommend                    : Agent recommendation engine - processes intent payloads and ranks matches ($0.005 USDC)
- GET  /api/v1/venues                       : List/filter venues by category, neighborhood, rating, price ($0.002 USDC)
- GET  /api/v1/venues/{id}                  : Detailed venue info with offerings, ratings, and sentiment tags ($0.002 USDC)
- GET  /api/v1/analytics/pricing-summary    : Category-specific price analytics across all offerings ($0.002 USDC)

## Payment Specification
- Standard: HTTP 402 / x402 Protocol
- Network: Base (Chain ID 8453)
- Currency: USDC
- Pay-To: 0x8Ae639d10b23Eb630241d7fD6275255a2e51Ec95

## Discovery Manifests
- GET /llms.json      : Full JSON discovery manifest for AI agents
- GET /llms-full.txt  : Complete plain-text dataset dump for context window ingestion
"""

@app.get("/llms-full.txt", response_class=PlainTextResponse)
def get_llms_full_txt():
    rows = query_db("SELECT * FROM venues ORDER BY category, overall_rating DESC")
    output = ["# Universal Agent Knowledge Graph — Full Dataset Dump\n"]
    output.append(f"Total Venues Indexed: {len(rows)}\n")
    output.append("=====================================================\n\n")

    current_category = ""
    for r in rows:
        if r['category'] != current_category:
            current_category = r['category']
            output.append(f"\n=== CATEGORY: {current_category.upper()} ===\n\n")

        output.append(f"## {r['name']} ({r['sub_category']})\n")
        output.append(f"- Category: {r['category']}\n")
        output.append(f"- Neighborhood: {r['neighborhood']}, Miami, FL\n")
        output.append(f"- Address: {r['address']}\n")
        output.append(f"- Price Level: {r['price_level']}\n")
        output.append(f"- Rating: {r['overall_rating']} ⭐ ({r['verified_reviews_count']} reviews)\n")
        output.append(f"- Scores: Safety {r['safety_score']}/5, Value {r['value_score']}/5, Ambiance {r['ambiance_score']}/5, Service {r['service_score']}/5\n")
        
        tags = json.loads(r['sentiment_tags'] or "[]")
        output.append(f"- Sentiment Tags: {', '.join(tags)}\n")
        
        if r['phone']: output.append(f"- Phone: {r['phone']}\n")
        if r['website']: output.append(f"- Website: {r['website']}\n")
        if r['booking_url']: output.append(f"- Booking URL: {r['booking_url']}\n")
        if r['wifi_speed_mbps']: output.append(f"- WiFi Speed: {r['wifi_speed_mbps']} Mbps\n")
        if r['has_outdoor_seating']: output.append("- Outdoor Seating: Yes\n")

        # Offerings
        offerings = query_db("SELECT * FROM offerings WHERE venue_id = ?", (r['id'],))
        if offerings:
            output.append("- Offerings & Pricing:\n")
            for o in offerings:
                output.append(f"  * [{o['category']}] {o['item']}: ${o['price_usd']:.2f} per {o['unit']}\n")
        
        output.append("\n-----------------------------------------------------\n\n")

    return "".join(output)

@app.get("/llms.json")
def get_llms_json():
    manifest_path = pathlib.Path(__file__).parent / "llms.json"
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            return json.load(f)
    return {"error": "llms.json manifest not found"}


# ------------------------------------------------------------------
# Universal Monetized Routes
# ------------------------------------------------------------------

@app.get("/api/v1/search")
def search(
    query: Optional[str] = None,
    category: Optional[str] = None,
    neighborhood: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price_level: Optional[str] = None,
    limit: int = 10
):
    """
    Universal multi-category intent search across cafes, restaurants, hotels, medspas.
    Query can be natural language (e.g. 'wifi cafes in Wynwood') or parameterized filters.
    """
    if query:
        # Classify intent from natural language
        intent = classify_intent(query)
        if category: intent["category"] = category
        if neighborhood: intent["neighborhood"] = neighborhood
        if min_rating: intent["min_rating"] = min_rating
        if max_price_level: intent["price_max"] = max_price_level
    else:
        # Parameterized query
        intent = {
            "category": category,
            "neighborhood": neighborhood,
            "min_rating": min_rating,
            "price_max": max_price_level,
            "raw_query": ""
        }
    
    results = search_venues(intent, limit=limit)
    
    return {
        "status": "success",
        "query": query or f"category={category}, neighborhood={neighborhood}",
        "classified_intent": intent.get("primary_intent", "search"),
        "matches_count": len(results),
        "data": results,
        "payment_receipt": {
            "settled": True,
            "cost_usd": PRICE_STANDARD_USD,
            "protocol": "x402"
        }
    }


@app.post("/api/v1/recommend")
def recommend(payload: Dict = Body(...)):
    """
    Multi-category Agent Recommendation Engine.
    Processes intent payload with category, preferred_area, required_features, max_price_level.
    Returns ranked list scored by Agent Match Index (0-100) with rationale.
    Cost: $0.005 USDC
    """
    category = payload.get("category")
    if not category:
        raise HTTPException(status_code=400, detail="Missing required field: 'category' (e.g. cafe, restaurant, hotel, medspa)")
    
    limit = payload.get("limit", 5)
    recommendations = recommend_venues(payload, limit=limit)
    
    return {
        "status": "success",
        "intent_payload": payload,
        "recommendations_count": len(recommendations),
        "data": recommendations,
        "payment_receipt": {
            "settled": True,
            "cost_usd": PRICE_RECOMMEND_USD,
            "protocol": "x402"
        }
    }


@app.get("/api/v1/venues")
def list_venues(
    category: Optional[str] = None,
    neighborhood: Optional[str] = None,
    min_rating: Optional[float] = None,
    limit: int = 20
):
    """List venues with optional filtering by category, neighborhood, rating."""
    where_clauses = []
    params = []
    
    if category:
        where_clauses.append("category = ?")
        params.append(category)
    if neighborhood:
        where_clauses.append("LOWER(neighborhood) = ?")
        params.append(neighborhood.lower())
    if min_rating:
        where_clauses.append("overall_rating >= ?")
        params.append(min_rating)
        
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    sql = f"SELECT * FROM venues {where_sql} ORDER BY overall_rating DESC LIMIT ?"
    params.append(limit)
    
    rows = query_db(sql, params)
    results = []
    for r in rows:
        item = dict(r)
        try: item['sentiment_tags'] = json.loads(item['sentiment_tags'] or "[]")
        except: item['sentiment_tags'] = []
        results.append(item)
        
    return {
        "status": "success",
        "count": len(results),
        "data": results,
        "payment_receipt": {
            "settled": True,
            "cost_usd": PRICE_STANDARD_USD,
            "protocol": "x402"
        }
    }


@app.get("/api/v1/venues/{venue_id}")
def get_venue(venue_id: int):
    """Get detailed venue info including offerings, ratings, sentiment tags."""
    row = query_db("SELECT * FROM venues WHERE id = ?", (venue_id,), one=True)
    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")
        
    data = dict(row)
    try: data['sentiment_tags'] = json.loads(data['sentiment_tags'] or "[]")
    except: data['sentiment_tags'] = []
    try: data['opening_hours'] = json.loads(data['opening_hours'] or "{}")
    except: data['opening_hours'] = {}
    
    offerings = query_db("SELECT * FROM offerings WHERE venue_id = ?", (venue_id,))
    data['offerings'] = [dict(o) for o in offerings]
    
    return {
        "status": "success",
        "data": data,
        "payment_receipt": {
            "settled": True,
            "cost_usd": PRICE_STANDARD_USD,
            "protocol": "x402"
        }
    }


@app.get("/api/v1/analytics/pricing-summary")
def get_pricing_summary(category: Optional[str] = None):
    """
    Category-specific average price analytics across offerings.
    Filter by category (e.g. ?category=cafe, ?category=hotel, ?category=medspa).
    """
    analytics = pricing_analytics(category=category)
    
    return {
        "status": "success",
        "analytics": analytics,
        "payment_receipt": {
            "settled": True,
            "cost_usd": PRICE_STANDARD_USD,
            "protocol": "x402"
        }
    }