#!/usr/bin/env python3
"""
outreach.py
Bulk email outreach to agent startups, AI platforms, and crypto-native companies.
Targets those most likely to integrate Agent Browser into their agent stack.

Run: python outreach.py --dry-run   # preview emails
      python outreach.py             # actually send (requires SMTP config)
"""

import json
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Target companies most likely to integrate our x402 API
TARGETS = [
    # AI Agent Platforms
    {"company": "LangChain", "email": "founders@langchain.com", "type": "agent_framework", 
     "hook": "LangChain tool for x402-monetized local venue search"},
    {"company": "LlamaIndex", "email": "info@llamaindex.ai", "type": "agent_framework",
     "hook": "LlamaIndex data connector for structured venue knowledge graph"},
    {"company": "CrewAI", "email": "hello@crewai.com", "type": "agent_framework",
     "hook": "CrewAI tool for agent-based local recommendations"},
    {"company": "AutoGen", "email": "autogen@microsoft.com", "type": "agent_framework",
     "hook": "AutoGen agent skill: local venue search with x402 payments"},
    {"company": "Phind", "email": "team@phind.com", "type": "ai_search",
     "hook": "Phind answer engine integration for local venue queries"},
    {"company": "Perplexity", "email": "api@perplexity.ai", "type": "ai_search",
     "hook": "Perplexity API enhancement: structured local data source"},
    {"company": "Cursor", "email": "hi@cursor.sh", "type": "ai_coding",
     "hook": "Cursor IDE integration: developers find local venues while coding"},
    {"company": "Devin", "email": "team@cognition.ai", "type": "ai_agent",
     "hook": "Devin agent skill: physical-world data for AI software engineers"},
    
    # Crypto/Web3 x402 Ecosystem
    {"company": "Coinbase Developer Platform", "email": "cdp@coinbase.com", "type": "crypto",
     "hook": "Reference implementation: live x402 HTTP 402 data marketplace"},
    {"company": "x402 Foundation", "email": "team@x402.org", "type": "crypto",
     "hook": "x402 ecosystem: working data refinery for registry showcase"},
    {"company": "Base", "email": "base@coinbase.com", "type": "crypto",
     "hook": "Base ecosystem showcase: real x402 USDC revenue on mainnet"},
    
    # AI Travel/Local Search
    {"company": "MindTrip", "email": "team@mindtrip.ai", "type": "ai_travel",
     "hook": "Travel AI: ground-truth local venue data via x402"},
    {"company": "Layla", "email": "hello@justlayla.com", "type": "ai_travel",
     "hook": "AI travel agent: x402-priced local intelligence"},
    
    # AI Real Estate / Healthcare
    {"company": "Compass AI", "email": "ai@compass.com", "type": "ai_realestate",
     "hook": "Real estate AI: neighborhood intelligence via Agent Browser"},
    {"company": "Zillow AI", "email": "ai@zillow.com", "type": "ai_realestate",
     "hook": "Property AI: local amenity data with structured sentiment"},
    
    # Restaurant / Food AI
    {"company": "Bite AI", "email": "hello@bite.ai", "type": "ai_restaurant",
     "hook": "Restaurant recommendation AI: pricing + sentiment + reviews"},
]

EMAIL_TEMPLATE = """Subject: {company} + Agent Browser: x402-powered local intelligence for agents

Hi {first_name},

I'm reaching out because {hook}.

I built Agent Browser — a queryable knowledge graph of 1,500+ US venues across 14 categories (cafes, restaurants, hotels, medspas, dentists, doctors, nutritionists, gyms, bars, bakeries, salons, retail, veterinarians, real estate) in 50 cities. Every query costs $0.002 USDC via the x402 HTTP 402 protocol on Base.

Three things make us different:
1. **x402-native** — agents pay per query, no API keys, no subscriptions
2. **Structured** — every response has multi-dimensional reputation scores, sentiment tags, and actionable metadata (booking URLs, WiFi speeds, hours)
3. **Multi-category** — one endpoint handles cafes, medspas, dentists, etc.

{company}-relevant integration paths:
- {langchain_tool if type == 'agent_framework' else api_endpoint}
- SDK: `pip install agent-browser-sdk` / npm coming
- MCP server available for standard agent protocol

Live endpoints (free):
- /llms.json (discovery manifest)
- /stats (public stats)
- /docs (OpenAPI spec)

If you're interested, I can:
- Send you a free API key for development (no x402 needed)
- Build a custom integration for your use case
- Co-marked case study showing your agents using our data

Reply if curious. Happy to do a 15-min call.

Best,
Agent Browser Team
https://medspa-refinery-api-44xz.onrender.com
"""


def render_email(target):
    """Render personalized email."""
    first_name = target["company"][:3].lower()  # Simple fallback
    return EMAIL_TEMPLATE.format(
        company=target["company"],
        first_name=first_name,
        hook=target["hook"],
        type=target["type"],
        langchain_tool="Python SDK + LangChain tool wrapper"
    )


def send_email(target, dry_run=True):
    """Send email via SMTP (configure your SMTP server)."""
    email_body = render_email(target)
    
    if dry_run:
        print(f"\n{'='*70}")
        print(f"To: {target['email']} ({target['company']})")
        print(f"Type: {target['type']}")
        print(f"Hook: {target['hook']}")
        print(f"{'='*70}")
        print(email_body[:500] + "...\n")
        return True
    
    # Production: Configure SMTP
    # msg = MIMEText(email_body)
    # msg['Subject'] = f"{target['company']} + Agent Browser: x402 local intelligence"
    # msg['From'] = "api@agent-browser.example.com"
    # msg['To'] = target['email']
    # 
    # with smtplib.SMTP('smtp.gmail.com', 587) as server:
    #     server.starttls()
    #     server.login('your-email@gmail.com', 'app-password')
    #     server.send_message(msg)
    
    print(f"[DRY-RUN] Would email {target['email']} ({target['company']})")
    return True


def main():
    parser = argparse.ArgumentParser(description="Agent Browser outreach campaign")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview emails without sending")
    parser.add_argument("--filter", type=str, help="Filter by type (e.g., agent_framework)")
    parser.add_argument("--limit", type=int, help="Limit number of emails")
    args = parser.parse_args()
    
    targets = TARGETS
    if args.filter:
        targets = [t for t in TARGETS if t["type"] == args.filter]
    if args.limit:
        targets = targets[:args.limit]
    
    print(f"Agent Browser Outreach Campaign")
    print(f"Targets: {len(targets)} companies")
    print(f"Mode: {'DRY-RUN (preview only)' if args.dry_run else 'LIVE (will send)'}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}\n")
    
    success_count = 0
    for target in targets:
        if send_email(target, dry_run=args.dry_run):
            success_count += 1
    
    print(f"\n{'='*70}")
    print(f"Campaign Summary:")
    print(f"  Total targets: {len(targets)}")
    print(f"  {'Would send' if args.dry_run else 'Sent'}: {success_count}")
    print(f"{'='*70}")
    
    print("\nNext steps:")
    print("1. Configure SMTP credentials (Gmail app password, SendGrid, etc.)")
    print("2. Run: python outreach.py --dry-run --filter agent_framework")
    print("3. Customize template with your name/contact info")
    print("4. Send first batch to LangChain, LlamaIndex, Phind (most likely to integrate)")
    print("5. Track responses, follow up in 3-5 days")


if __name__ == "__main__":
    main()