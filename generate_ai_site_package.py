#!/usr/bin/env python3
"""
generate_ai_site_package.py
Method 2 — AI Readiness Agency Optimization Bundle Generator

Reads clinic records from medspa_data.db and produces a per-clinic
optimization package containing:
  1) llms.txt + llms-full.txt (machine-readable index)
  2) MedicalBusiness + OfferCatalog JSON-LD schema (for <head> injection)
  3) FAQ page (plain text, LLM-optimized structure)
  4) README.md with deployment instructions

Output: ./ai_site_packages/<clinic_slug>/
"""

from __future__ import annotations

import json
import sqlite3
import os
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "medspa_data.db"
OUTPUT_ROOT = Path(__file__).resolve().parent / "ai_site_packages"

# ------------------------------------------------------------------ #
# Database helpers
# ------------------------------------------------------------------ #
def fetch_clinics() -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM clinics ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    for r in rows:
        try:
            r["services"] = json.loads(r.pop("services_json", "[]"))
        except json.JSONDecodeError:
            r["services"] = []
    return rows


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("&", "and").replace(".", "").replace(",", "")


# ------------------------------------------------------------------ #
# 1) llms.txt / llms-full.txt
# ------------------------------------------------------------------ #
def generate_llms_txt(clinic: dict[str, Any]) -> str:
    services_summary = "\n".join(
        f"- {s['category']}: {s['item']} (${s['price_usd']:.2f}/{s['unit']})"
        for s in clinic["services"]
    )
    return f"""# {clinic['name']} — AI Agent Index
> Machine-readable profile for LLM crawlers (ChatGPT, Claude, Gemini, Perplexity).

## Business Identity
- **Name**: {clinic['name']}
- **Address**: {clinic['address']}
- **Phone**: {clinic['phone']}
- **Website**: {clinic['website']}
- **Rating**: {clinic['rating']} ⭐ ({clinic['reviews_count']} reviews)
- **AI Visibility Score**: {clinic['ai_visibility_score']}/100
- **Last Updated**: {datetime.now().isoformat()}

## Services & Pricing
{services_summary}

## Structured Data Endpoints
- JSON-LD MedicalBusiness + OfferCatalog: /structured-data.jsonld
- Full FAQ for LLM indexing: /faq.txt
- Machine-readable service list: /services.json

## Payment (Agent Economy)
- Protocol: x402 / HTTP 402
- Price: $0.002 USDC per query
- Network: Base (chain 8453)
- Wallet: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
- Scheme: exact

## Crawler Instructions
- Allow: All AI agents (GPTBot, ClaudeBot, Google-Extended, PerplexityBot, etc.)
- Disallow: /admin, /private
- Sitemap: /sitemap.xml
"""


def generate_llms_full_txt(clinic: dict[str, Any]) -> str:
    out = []
    out.append(f"# {clinic['name']} — Complete Dataset for LLM Context Window")
    out.append(f"Generated: {datetime.now().isoformat()}\n")
    out.append("## Business Details")
    out.append(f"- Name: {clinic['name']}")
    out.append(f"- Address: {clinic['address']}")
    out.append(f"- Phone: {clinic['phone']}")
    out.append(f"- Website: {clinic['website']}")
    out.append(f"- Rating: {clinic['rating']} ({clinic['reviews_count']} reviews)")
    out.append(f"- AI Visibility Score: {clinic['ai_visibility_score']}/100")
    out.append("\n## Services & Pricing (Complete)")
    for s in clinic["services"]:
        out.append(f"- [{s['category']}] {s['item']}: ${s['price_usd']:.2f} per {s['unit']}")
    out.append("\n## JSON-LD Schema Available At")
    out.append("/structured-data.jsonld (MedicalBusiness + OfferCatalog)")
    out.append("\n## FAQ for LLM Retrieval")
    out.append("/faq.txt (structured Q&A)")
    return "\n".join(out)


# ------------------------------------------------------------------ #
# 2) JSON-LD: MedicalBusiness + OfferCatalog
# ------------------------------------------------------------------ #
def generate_json_ld(clinic: dict[str, Any]) -> dict[str, Any]:
    # Build offers from services
    offers = []
    for s in clinic["services"]:
        offers.append({
            "@type": "Offer",
            "name": s["item"],
            "description": f"{s['category']} treatment: {s['item']}",
            "price": f"{s['price_usd']:.2f}",
            "priceCurrency": "USD",
            "unitCode": s["unit"].upper(),  # e.g., UNIT, SYRINGE, SESSION
            "availability": "https://schema.org/InStock",
            "category": s["category"]
        })

    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "MedicalBusiness",
                "@id": f"{clinic['website']}#business",
                "name": clinic["name"],
                "description": f"Premier medical aesthetics and wellness clinic in {clinic['city']}, {clinic['state']}. Specializing in injectables, laser treatments, body contouring, and wellness programs.",
                "url": clinic["website"],
                "telephone": clinic["phone"],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": clinic["address"].split(",")[0].strip(),
                    "addressLocality": clinic["city"],
                    "addressRegion": clinic["state"],
                    "postalCode": clinic["address"].split(",")[-1].strip().split()[-1],
                    "addressCountry": "US"
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": 25.7617,  # Miami approx
                    "longitude": -80.1918
                },
                "priceRange": "$$$",
                "currenciesAccepted": "USD",
                "paymentAccepted": "Cash, Credit Card, Insurance, HSA/FSA",
                "openingHoursSpecification": [
                    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Monday", "opens": "09:00", "closes": "18:00"},
                    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Tuesday", "opens": "09:00", "closes": "18:00"},
                    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Wednesday", "opens": "09:00", "closes": "18:00"},
                    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Thursday", "opens": "09:00", "closes": "18:00"},
                    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Friday", "opens": "09:00", "closes": "18:00"},
                    {"@type": "OpeningHoursSpecification", "dayOfWeek": "Saturday", "opens": "09:00", "closes": "14:00"}
                ],
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": clinic["rating"],
                    "reviewCount": clinic["reviews_count"],
                    "bestRating": "5",
                    "worstRating": "1"
                },
                "medicalSpecialty": ["Dermatology", "Plastic Surgery", "Aesthetic Medicine"],
                "knowsAbout": [s["item"] for s in clinic["services"]],
                "makesOffer": {
                    "@type": "OfferCatalog",
                    "name": f"{clinic['name']} Service Catalog",
                    "itemListElement": [
                        {
                            "@type": "OfferCatalog",
                            "name": cat,
                            "itemListElement": [
                                {
                                    "@type": "Offer",
                                    "name": s["item"],
                                    "description": f"{s['category']}: {s['item']}",
                                    "price": f"{s['price_usd']:.2f}",
                                    "priceCurrency": "USD",
                                    "unitCode": s["unit"].upper(),
                                    "availability": "https://schema.org/InStock"
                                }
                                for s in clinic["services"] if s["category"] == cat
                            ]
                        }
                        for cat in sorted(set(s["category"] for s in clinic["services"]))
                    ]
                }
            },
            # WebSite for search action
            {
                "@type": "WebSite",
                "@id": f"{clinic['website']}#website",
                "url": clinic["website"],
                "name": clinic["name"],
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": f"{clinic['website']}/search?q={{search_term_string}}"
                    },
                    "query-input": "required name=search_term_string"
                }
            }
        ]
    }
    return jsonld


# ------------------------------------------------------------------ #
# 3) FAQ Page (LLM-optimized plain text)
# ------------------------------------------------------------------ #
def generate_faq_txt(clinic: dict[str, Any]) -> str:
    out = []
    out.append(f"# {clinic['name']} — Frequently Asked Questions")
    out.append(f"Structured for LLM Retrieval (ChatGPT, Claude, Gemini, Perplexity)")
    out.append(f"Generated: {datetime.now().isoformat()}\n")
    out.append("=" * 60)
    out.append("")

    # General FAQs
    out.append("## General Questions")
    out.append("")
    out.append("### Q: Where is {name} located?".format(name=clinic['name']))
    out.append(f"A: {clinic['name']} is located at {clinic['address']}. We serve clients throughout {clinic['city']}, {clinic['state']} and surrounding areas.")
    out.append("")
    out.append("### Q: What are your hours of operation?")
    out.append("A: Monday–Friday 9:00 AM – 6:00 PM, Saturday 9:00 AM – 2:00 PM, Closed Sunday.")
    out.append("")
    out.append("### Q: How can I book an appointment?")
    out.append(f"A: Call {clinic['phone']} or visit {clinic['website']} to book online. We recommend booking 1–2 weeks in advance for popular treatments.")
    out.append("")
    out.append("### Q: Do you accept insurance?")
    out.append("A: We accept HSA/FSA for qualified medical treatments. Cosmetic treatments are typically self-pay. Contact our office for insurance verification.")
    out.append("")

    # Treatment-specific FAQs
    out.append("## Treatment-Specific Questions")
    out.append("")

    categories = sorted(set(s["category"] for s in clinic["services"]))
    for cat in categories:
        cat_services = [s for s in clinic["services"] if s["category"] == cat]
        out.append(f"### {cat}")
        out.append("")
        for s in cat_services:
            item = s["item"]
            price = f"${s['price_usd']:.2f}"
            unit = s["unit"]
            out.append(f"#### Q: How much does {item} cost?")
            out.append(f"A: {item} is {price} per {unit}.")
            out.append("")
            out.append(f"#### Q: What is {item}?")
            out.append(f"A: {item} is a {cat.lower()} treatment offered at {clinic['name']}. Consult our specialists for personalized recommendations.")
            out.append("")

    # AI Agent FAQs
    out.append("## For AI Agents & Automated Systems")
    out.append("")
    out.append("### Q: What is your x402 payment endpoint?")
    out.append("A: All API endpoints require HTTP 402 payment of $0.002 USDC via x402 protocol on Base network (chain 8453). Wallet: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
    out.append("")
    out.append("### Q: Where can I find your machine-readable service data?")
    out.append(f"A: Structured data available at {clinic['website']}/structured-data.jsonld (JSON-LD), {clinic['website']}/services.json, {clinic['website']}/llms.txt, and {clinic['website']}/faq.txt")
    out.append("")

    return "\n".join(out)


# ------------------------------------------------------------------ #
# Package assembly
# ------------------------------------------------------------------ #
def build_package(clinic: dict[str, Any]) -> Path:
    clinic_slug = slugify(clinic["name"])
    out_dir = OUTPUT_ROOT / clinic_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) llms.txt
    (out_dir / "llms.txt").write_text(generate_llms_txt(clinic), encoding="utf-8")
    # 2) llms-full.txt
    (out_dir / "llms-full.txt").write_text(generate_llms_full_txt(clinic), encoding="utf-8")
    # 3) JSON-LD
    (out_dir / "structured-data.jsonld").write_text(
        json.dumps(generate_json_ld(clinic), indent=2), encoding="utf-8"
    )
    # 4) FAQ
    (out_dir / "faq.txt").write_text(generate_faq_txt(clinic), encoding="utf-8")
    # 5) Services JSON (flat)
    (out_dir / "services.json").write_text(
        json.dumps(clinic["services"], indent=2), encoding="utf-8"
    )
    # 6) README
    readme = f"""# {clinic['name']} — AI Readiness Optimization Package

Generated: {datetime.now().isoformat()}
AI Visibility Score: {clinic['ai_visibility_score']}/100

## Contents
| File | Purpose | Deploy To |
|------|---------|-----------|
| `llms.txt` | Machine-readable index for LLM crawlers | `/llms.txt` (root) |
| `llms-full.txt` | Full dataset for context window ingestion | `/llms-full.txt` |
| `structured-data.jsonld` | MedicalBusiness + OfferCatalog schema | `<head>` of homepage |
| `faq.txt` | Structured Q&A for LLM retrieval | `/faq.txt` |
| `services.json` | Flat service list for agents | `/services.json` |

## Quick Deploy (Static Site / WordPress / Webflow / Squarespace)

### 1. JSON-LD Schema
Paste `structured-data.jsonld` into your homepage `<head>`:
```html
<script type="application/ld+json">
{json.dumps(generate_json_ld(clinic), indent=2)}
</script>
```

### 2. llms.txt / llms-full.txt / faq.txt / services.json
Upload to your web root (or configure rewrites):
- `yoursite.com/llms.txt`
- `yoursite.com/llms-full.txt`
- `yoursite.com/faq.txt`
- `yoursite.com/services.json`

### 3. robots.txt (add to existing)
```
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: https://yoursite.com/sitemap.xml
```

### 4. Verify
- Test JSON-LD: https://validator.schema.org/
- Test llms.txt: https://llmstxt.org/validate
- Check AI visibility: Ask ChatGPT "What services does {clinic['name']} offer?"

## AI Visibility Score Interpretation
- **90-100**: LLM-optimized — appears in most agent responses
- **70-89**: Good — appears in some agent responses
- **50-69**: Moderate — partial coverage
- **<50**: Poor — invisible to most AI agents (agency upsell target)

Current Score: **{clinic['ai_visibility_score']}/100**

## Next Steps (AI Readiness Agency Services)
1. **Schema Audit** — Validate all schema markup across site
2. **Content Optimization** — Rewrite service pages for LLM retrieval
3. **llms.txt Deployment** — Host at root + submit to indexes
4. **MCP Server Setup** — Expose data via Model Context Protocol
5. **x402 Monetization** — Enable agent micropayments for premium data

---
*Generated by AI Readiness Agency — Method 2 Pipeline*
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    return out_dir


def main():
    print("🔍 Fetching clinics from database...")
    clinics = fetch_clinics()
    print(f"📦 Found {len(clinics)} clinics")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    for clinic in clinics:
        print(f"\n🏗️  Building package for: {clinic['name']}")
        pkg_dir = build_package(clinic)
        print(f"   ✅ Output: {pkg_dir}")

    print(f"\n🎉 All packages generated in: {OUTPUT_ROOT}")
    print("\n📁 Structure:")
    for clinic in clinics:
        slug = slugify(clinic["name"])
        print(f"  ai_site_packages/{slug}/")
        for f in ["llms.txt", "llms-full.txt", "structured-data.jsonld", "faq.txt", "services.json", "README.md"]:
            print(f"    ├── {f}")


if __name__ == "__main__":
    main()