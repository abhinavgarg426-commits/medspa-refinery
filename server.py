import json
import sqlite3
import base64
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

DB_PATH = "medspa_data.db"
RECEIVING_WALLET = "0x8Ae639d10b23Eb630241d7fD6275255a2e51Ec95"
PRICE_PER_REQUEST_USD = 0.002
PRICE_IN_USDC_UNITS = 2000

app = FastAPI(
    title="Miami MedSpa Niche Data Refinery API",
    description="Machine-readable data refinery powering AI agents with micro-paid clinic pricing & visibility analytics.",
    version="1.0.0"
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
# Phase 3: HTTP 402 / x402 Payment Required Middleware (class-based)
# ------------------------------------------------------------------
class X402PaymentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = ["/", "/docs", "/openapi.json", "/llms.txt", "/llms-full.txt", "/health"]
        if request.url.path in public_paths:
            return await call_next(request)

        payment_sig = request.headers.get("PAYMENT-SIGNATURE") or request.headers.get("X-Payment-Proof")
        mock_auth = request.headers.get("X-Mock-Payment-Paid")

        if not payment_sig and not mock_auth:
            x402_spec = {
                "x402_version": "1.0",
                "title": "Miami MedSpa Data Endpoint",
                "price": {
                    "amount_usd": PRICE_PER_REQUEST_USD,
                    "amount_units": PRICE_IN_USDC_UNITS,
                    "currency": "USDC",
                    "network": "base",
                    "chain_id": 8453
                },
                "pay_to": RECEIVING_WALLET,
                "scheme": "exact",
                "resource": request.url.path,
                "instruction": "Sign payment payload with your Web3 wallet or USDC permit and include in PAYMENT-SIGNATURE header."
            }

            encoded_spec = base64.b64encode(json.dumps(x402_spec).encode('utf-8')).decode('utf-8')

            headers = {
                "PAYMENT-REQUIRED": encoded_spec,
                "X-Payment-Address": RECEIVING_WALLET,
                "X-Payment-Price": f"{PRICE_PER_REQUEST_USD} USDC",
                "X-Payment-Network": "base",
                "WWW-Authenticate": f'x402 realm="Data Refinery", price="{PRICE_PER_REQUEST_USD}", address="{RECEIVING_WALLET}"'
            }

            return JSONResponse(
                status_code=402,
                content={
                    "error": "Payment Required",
                    "status_code": 402,
                    "message": f"This endpoint requires a micro-payment of ${PRICE_PER_REQUEST_USD} USDC via x402 protocol.",
                    "x402_details": x402_spec
                },
                headers=headers
            )

        return await call_next(request)

app.add_middleware(X402PaymentMiddleware)

# ------------------------------------------------------------------
# Phase 2: LLM Indexing
# ------------------------------------------------------------------
@app.get("/llms.txt", response_class=PlainTextResponse)
def get_llms_txt():
    return """# Miami MedSpa & Aesthetic Clinic Data Refinery
> Machine-readable structured database of local aesthetic clinics, pricing, services, and AI visibility readiness scores in Miami, FL.

## Core Endpoints
- GET /api/v1/clinics: Returns full list of medspas, location, rating, and AI visibility score. (Cost: $0.002 USDC via x402)
- GET /api/v1/clinics/{id}: Returns specific clinic info and itemized pricing list (Botox, fillers, lasers, weight loss). (Cost: $0.002 USDC via x402)
- GET /api/v1/search?service=botox: Query clinics offering specific treatments and compare prices across Miami. (Cost: $0.002 USDC via x402)

## Data Specification
- Format: JSON
- Payment Standard: HTTP 402 / x402 Protocol (Base Network / USDC)
- Pay-To Address: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e

## Full Documentation & Dump
- GET /llms-full.txt : Full plain-text dump for context window ingestion.
"""

@app.get("/llms-full.txt", response_class=PlainTextResponse)
def get_llms_full_txt():
    rows = query_db("SELECT * FROM clinics")
    output = ["# Full Miami MedSpa Dataset Dump\n"]
    output.append(f"Total Clinics Registered: {len(rows)}\n")
    output.append("=====================================================\n\n")

    for r in rows:
        output.append(f"## Clinic: {r['name']}\n")
        output.append(f"- City: {r['city']}, {r['state']}\n")
        output.append(f"- Address: {r['address']}\n")
        output.append(f"- Phone: {r['phone']}\n")
        output.append(f"- Website: {r['website']}\n")
        output.append(f"- Rating: {r['rating']} ⭐ ({r['reviews_count']} reviews)\n")
        output.append(f"- AI Visibility Score: {r['ai_visibility_score']}/100\n")
        output.append("- Services & Pricing:\n")
        
        services = json.loads(r['services_json'])
        for s in services:
            output.append(f"  * [{s['category']}] {s['item']}: ${s['price_usd']:.2f} per {s['unit']}\n")
        output.append("\n-----------------------------------------------------\n\n")

    return "".join(output)

# ------------------------------------------------------------------
# Public & Monetized API Routes
# ------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Miami MedSpa Data Refinery",
        "protocol": "x402 HTTP 402 Enabled",
        "llms_txt": "/llms.txt",
        "llms_full_txt": "/llms-full.txt",
        "api_docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/v1/clinics")
def list_clinics(city: Optional[str] = None):
    if city:
        rows = query_db("SELECT * FROM clinics WHERE LOWER(city) = LOWER(?)", (city,))
    else:
        rows = query_db("SELECT * FROM clinics")

    results = []
    for r in rows:
        item = dict(r)
        item['services'] = json.loads(item.pop('services_json'))
        results.append(item)

    return {
        "status": "success",
        "count": len(results),
        "data": results,
        "payment_receipt": {
            "settled": True,
            "cost_usd": PRICE_PER_REQUEST_USD,
            "protocol": "x402"
        }
    }

@app.get("/api/v1/clinics/{clinic_id}")
def get_clinic_by_id(clinic_id: int):
    row = query_db("SELECT * FROM clinics WHERE id = ?", (clinic_id,), one=True)
    if not row:
        raise HTTPException(status_code=404, detail="Clinic not found")

    data = dict(row)
    data['services'] = json.loads(data.pop('services_json'))
    return {
        "status": "success",
        "data": data,
        "payment_receipt": {
            "settled": True,
            "cost_usd": PRICE_PER_REQUEST_USD,
            "protocol": "x402"
        }
    }

@app.get("/api/v1/search")
def search_treatments(treatment: str):
    rows = query_db("SELECT * FROM clinics")
    matches = []
    
    treatment_lower = treatment.lower()
    for r in rows:
        clinic = dict(r)
        services = json.loads(clinic.pop('services_json'))
        matching_services = [s for s in services if treatment_lower in s['item'].lower() or treatment_lower in s['category'].lower()]
        if matching_services:
            clinic['matching_services'] = matching_services
            matches.append(clinic)

    return {
        "status": "success",
        "query": treatment,
        "matches_count": len(matches),
        "data": matches
    }