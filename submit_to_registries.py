#!/usr/bin/env python3
"""
submit_to_registries.py
Submit our x402 API endpoint to public AI agent registries and x402 ecosystem aggregators.

Usage: python submit_to_registries.py
"""

import httpx
import json
import os
import sys
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "https://medspa-refinery-api-44xz.onrender.com"
LLMS_JSON_URL = f"{API_BASE_URL}/llms.json"
REPO_URL = "https://github.com/abhinavgarg426-commits/medspa-refinery"

# Target registries (publicly known aggregators)
# Note: Some of these may not exist yet or require API keys.
# This script provides the framework; update with real endpoints as they launch.

REGISTRIES = [
    {
        "name": "x402 Protocol Registry",
        "url": "https://api.x402.org/v1/register",
        "method": "POST",
        "description": "Official x402 protocol service directory",
        "payload_template": lambda: {
            "manifest_url": LLMS_JSON_URL,
            "api_base_url": API_BASE_URL,
            "repository_url": REPO_URL,
            "contact": "api@medspa-refinery.example.com"
        }
    },
    {
        "name": "MCP Registry (Model Context Protocol)",
        "url": "https://mcp-registry.example.com/v1/servers",
        "method": "POST",
        "description": "MCP server directory for tool discovery",
        "payload_template": lambda: {
            "server_name": "miami-medspa-refinery",
            "manifest_url": LLMS_JSON_URL,
            "transport": "stdio",
            "repository_url": REPO_URL,
            "capabilities": ["search", "pricing", "visibility"]
        }
    },
    {
        "name": "Agent Marketplace (Hypothetical)",
        "url": "https://agent-marketplace.example.com/api/v1/services",
        "method": "POST",
        "description": "AI agent service marketplace",
        "payload_template": lambda: {
            "name": "Miami MedSpa Data Refinery",
            "description": "Structured clinic pricing & AI visibility data via x402 micropayments",
            "manifest_url": LLMS_JSON_URL,
            "base_url": API_BASE_URL,
            "pricing": {
                "model": "per_request",
                "currency": "USDC",
                "amount": 0.002,
                "network": "base"
            },
            "categories": ["healthcare", "pricing", "local-data", "ai-readiness"]
        }
    },
    {
        "name": "LLMs.txt Directory (llmstxt.org)",
        "url": "https://llmstxt.org/api/submit",
        "method": "POST",
        "description": "Community llms.txt index aggregator",
        "payload_template": lambda: {
            "url": f"{API_BASE_URL}/llms.txt",
            "json_manifest": LLMS_JSON_URL,
            "repo": REPO_URL
        }
    },
    {
        "name": "AI Tool Index (hypothetical)",
        "url": "https://aitoolindex.io/api/v1/tools",
        "method": "POST",
        "description": "Directory of AI-callable tools and APIs",
        "payload_template": lambda: {
            "name": "Miami MedSpa Data Refinery",
            "type": "data-api",
            "protocol": "x402",
            "endpoints": [
                {"path": "/api/v1/search", "description": "Search treatment pricing"},
                {"path": "/api/v1/clinics", "description": "List all clinics"},
                {"path": "/api/v1/clinics/{id}", "description": "Get clinic details"}
            ],
            "manifest": LLMS_JSON_URL,
            "docs": f"{API_BASE_URL}/docs"
        }
    }
]

async def submit_to_registry(client: httpx.AsyncClient, registry: Dict) -> Dict:
    """Submit to a single registry."""
    payload = registry["payload_template"]()
    
    print(f"\n[*] Submitting to {registry['name']}...")
    print(f"    URL: {registry['url']}")
    print(f"    Method: {registry['method']}")
    
    try:
        response = await client.request(
            method=registry["method"],
            url=registry["url"],
            json=payload,
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Miami-MedSpa-Refinery/1.0 (Registration Bot)"
            }
        )
        
        result = {
            "registry": registry["name"],
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response": response.text[:500] if response.text else ""
        }
        
        if result["success"]:
            print(f"    [+] SUCCESS: {response.status_code}")
        else:
            print(f"    [!] FAILED: {response.status_code} - {result['response']}")
        
        return result
        
    except httpx.TimeoutException:
        print(f"    [X] TIMEOUT: Request took >30s")
        return {"registry": registry["name"], "status_code": 0, "success": False, "response": "Timeout"}
    except httpx.ConnectError as e:
        print(f"    [X] CONNECTION ERROR: {e}")
        return {"registry": registry["name"], "status_code": 0, "success": False, "response": str(e)}
    except Exception as e:
        print(f"    [X] ERROR: {type(e).__name__}: {e}")
        return {"registry": registry["name"], "status_code": 0, "success": False, "response": str(e)}


async def main():
    print("=" * 60)
    print("Miami MedSpa Data Refinery - Registry Submission")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Manifest URL: {LLMS_JSON_URL}")
    print(f"Repository: {REPO_URL}")
    print(f"Registries to submit: {len(REGISTRIES)}")
    
    # First verify our manifest is accessible
    print("\n[*] Verifying manifest accessibility...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(LLMS_JSON_URL, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                print(f"[+] Manifest verified: {data.get('name', 'Unknown')} v{data.get('version', '?')}")
            else:
                print(f"[!] Manifest check failed: {resp.status_code}")
                return 1
    except Exception as e:
        print(f"[X] Cannot reach manifest: {e}")
        return 1
    
    # Submit to all registries
    results = []
    async with httpx.AsyncClient() as client:
        for registry in REGISTRIES:
            result = await submit_to_registry(client, registry)
            results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUBMISSION SUMMARY")
    print("=" * 60)
    success_count = sum(1 for r in results if r["success"])
    for r in results:
        status = "[+] OK" if r["success"] else "[X] FAIL"
        print(f"  {status}  {r['registry']} ({r['status_code']})")
    
    print(f"\nTotal: {success_count}/{len(REGISTRIES)} successful")
    
    if success_count == 0:
        print("\n[!] Note: Most registries are hypothetical/future endpoints.")
        print("    Update REGISTRIES list with real endpoints as they launch.")
        print("    Current verified: /llms.json, /llms.txt accessible at:")
        print(f"      {LLMS_JSON_URL}")
        print(f"      {API_BASE_URL}/llms.txt")
    
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))