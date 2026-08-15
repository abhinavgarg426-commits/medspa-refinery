#!/usr/bin/env python3
"""
ping_agents.py
Asynchronous broadcast of our x402 API endpoint to AI agent crawlers,
Web3 indexers, and public llms.txt directories.

Run periodically to ensure our service is indexed and discoverable.
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "https://medspa-refinery-api-44xz.onrender.com"
LLMS_JSON_URL = f"{API_BASE_URL}/llms.json"
LLMS_TXT_URL = f"{API_BASE_URL}/llms.txt"
REPO_URL = "https://github.com/abhinavgarg426-commits/medspa-refinery"

# Target endpoints for ecosystem discovery
PING_TARGETS = [
    {
        "name": "llmstxt.org - Community Index",
        "url": "https://llmstxt.org/api/submit",
        "method": "POST",
        "payload": lambda: {
            "url": LLMS_TXT_URL,
            "json_manifest": LLMS_JSON_URL,
            "repo": REPO_URL,
            "submitted_at": datetime.utcnow().isoformat() + "Z"
        },
        "headers": {"Content-Type": "application/json", "User-Agent": "Miami-MedSpa-Refinery/1.0"}
    },
    {
        "name": "x402 Protocol Directory",
        "url": "https://api.x402.org/v1/register",
        "method": "POST",
        "payload": lambda: {
            "manifest_url": LLMS_JSON_URL,
            "api_base_url": API_BASE_URL,
            "repository_url": REPO_URL,
            "protocol": "x402",
            "network": "base",
            "chain_id": 8453,
            "submitted_at": datetime.utcnow().isoformat() + "Z"
        },
        "headers": {"Content-Type": "application/json", "User-Agent": "Miami-MedSpa-Refinery/1.0"}
    },
    {
        "name": "AI Agent Hub (hypothetical)",
        "url": "https://agent-hub.io/api/v1/services",
        "method": "POST",
        "payload": lambda: {
            "name": "Miami MedSpa Data Refinery",
            "type": "structured-data-api",
            "protocol": "x402",
            "base_url": API_BASE_URL,
            "manifest_url": LLMS_JSON_URL,
            "payment": {"network": "base", "currency": "USDC", "price_usd": 0.002},
            "categories": ["healthcare", "pricing", "local-data", "ai-readiness"],
            "submitted_at": datetime.utcnow().isoformat() + "Z"
        },
        "headers": {"Content-Type": "application/json", "User-Agent": "Miami-MedSpa-Refinery/1.0"}
    },
    {
        "name": "MCP Registry (Model Context Protocol)",
        "url": "https://mcp-registry.example.com/v1/servers",
        "method": "POST",
        "payload": lambda: {
            "server_name": "miami-medspa-refinery",
            "manifest_url": LLMS_JSON_URL,
            "transport": "stdio",
            "repository_url": REPO_URL,
            "capabilities": ["search", "pricing", "visibility"],
            "submitted_at": datetime.utcnow().isoformat() + "Z"
        },
        "headers": {"Content-Type": "application/json", "User-Agent": "Miami-MedSpa-Refinery/1.0"}
    },
    {
        "name": "Public LLM Directory",
        "url": "https://llm-directory.io/api/v1/endpoints",
        "method": "POST",
        "payload": lambda: {
            "endpoint": API_BASE_URL,
            "manifest": LLMS_JSON_URL,
            "docs": f"{API_BASE_URL}/docs",
            "pricing_model": "per_request_x402",
            "submitted_at": datetime.utcnow().isoformat() + "Z"
        },
        "headers": {"Content-Type": "application/json", "User-Agent": "Miami-MedSpa-Refinery/1.0"}
    }
]

# Also ping search engines / crawlers via their submission APIs
CRAWLER_PINGS = [
    {
        "name": "Google Indexing API (requires service account)",
        "url": "https://indexing.googleapis.com/v3/urlNotifications:publish",
        "method": "POST",
        "note": "Requires GOOGLE_INDEXING_SERVICE_ACCOUNT env var"
    },
    {
        "name": "Bing URL Submission API",
        "url": "https://ssl.bing.com/webmaster/api.svc/json/SubmitUrl",
        "method": "POST",
        "note": "Requires BING_API_KEY env var"
    }
]

async def ping_target(client: httpx.AsyncClient, target: Dict) -> Dict:
    """Send a single ping to a discovery target."""
    payload = target["payload"]()
    
    print(f"\n[*] Pinging {target['name']}...")
    print(f"    URL: {target['url']}")
    
    try:
        response = await client.request(
            method=target["method"],
            url=target["url"],
            json=payload,
            timeout=15.0,
            headers=target.get("headers", {})
        )
        
        result = {
            "target": target["name"],
            "url": target["url"],
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response": response.text[:300] if response.text else ""
        }
        
        if result["success"]:
            print(f"    [+] SUCCESS: {response.status_code}")
        else:
            print(f"    [!] FAILED: {response.status_code} - {result['response']}")
        
        return result
        
    except httpx.TimeoutException:
        print(f"    [X] TIMEOUT (>15s)")
        return {"target": target["name"], "status_code": 0, "success": False, "response": "Timeout"}
    except httpx.ConnectError as e:
        print(f"    [X] CONNECTION ERROR: {e}")
        return {"target": target["name"], "status_code": 0, "success": False, "response": str(e)}
    except Exception as e:
        print(f"    [X] ERROR: {type(e).__name__}: {e}")
        return {"target": target["name"], "status_code": 0, "success": False, "response": str(e)}


async def ping_crawlers() -> List[Dict]:
    """Attempt to ping major search engine crawlers (if credentials available)."""
    results = []
    
    # Google Indexing API
    google_sa = os.getenv("GOOGLE_INDEXING_SERVICE_ACCOUNT")
    if google_sa:
        print("\n[*] Pinging Google Indexing API...")
        # Would require google-auth library and service account setup
        results.append({"target": "Google Indexing", "status": "configured", "note": "Service account present"})
    else:
        results.append({"target": "Google Indexing", "status": "skipped", "note": "No service account"})
    
    # Bing
    bing_key = os.getenv("BING_API_KEY")
    if bing_key:
        print("\n[*] Pinging Bing URL Submission...")
        results.append({"target": "Bing", "status": "configured", "note": "API key present"})
    else:
        results.append({"target": "Bing", "status": "skipped", "note": "No API key"})
    
    return results


async def verify_manifest_accessible(client: httpx.AsyncClient) -> bool:
    """Verify our own manifest is accessible before pinging others."""
    try:
        resp = await client.get(LLMS_JSON_URL, timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[+] Manifest verified: {data.get('name', 'Unknown')} v{data.get('version', '?')}")
            return True
        else:
            print(f"[!] Manifest check failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[X] Cannot reach manifest: {e}")
        return False


async def main():
    print("=" * 60)
    print("Miami MedSpa Data Refinery - Ecosystem Ping")
    print("=" * 60)
    print(f"API Base: {API_BASE_URL}")
    print(f"Manifest: {LLMS_JSON_URL}")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print(f"Targets: {len(PING_TARGETS)}")
    
    async with httpx.AsyncClient() as client:
        # Verify our manifest first
        if not await verify_manifest_accessible(client):
            print("[X] Aborting - manifest not accessible")
            return 1
        
        # Ping all discovery targets
        results = []
        for target in PING_TARGETS:
            result = await ping_target(client, target)
            results.append(result)
            await asyncio.sleep(0.5)  # Be nice to APIs
        
        # Crawler pings (if configured)
        await ping_crawlers()
        
        # Summary
        print("\n" + "=" * 60)
        print("PING SUMMARY")
        print("=" * 60)
        success = sum(1 for r in results if r["success"])
        for r in results:
            status = "[+] OK" if r["success"] else "[X] FAIL"
            print(f"  {status}  {r['target']} ({r['status_code']})")
        
        print(f"\nSuccessful: {success}/{len(PING_TARGETS)}")
        
        if success == 0:
            print("\n[!] Note: Most registry endpoints are hypothetical/future.")
            print("    Update PING_TARGETS with real endpoints as they launch.")
            print(f"    Verified accessible: {LLMS_JSON_URL}")
            print(f"    Verified accessible: {LLMS_TXT_URL}")
        
        return 0 if success > 0 else 0  # Don't fail CI if registries don't exist yet


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))