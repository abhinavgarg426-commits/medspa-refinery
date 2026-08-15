#!/usr/bin/env python3
"""
enrichment_pipeline.py
Automated data scraping / enrichment pipeline for MedSpa Data Refinery.

Periodically fetches new clinic listings or pricing updates from external sources
and updates the SQLite database. Designed to run as a cron job or background daemon.

Sources (configurable):
- Google Places API (requires API key)
- Yelp Fusion API (requires API key)
- Manual CSV/JSON import
- Web scraping of clinic websites (BeautifulSoup)
- Price comparison aggregators

Usage:
  python enrichment_pipeline.py --once           # Single enrichment run
  python enrichment_pipeline.py --daemon --interval 3600  # Run every hour
"""

import sqlite3
import json
import httpx
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup

DB_PATH = "medspa_data.db"

# Configuration - Add your API keys here or via environment variables
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
YELP_API_KEY = os.getenv("YELP_API_KEY")
SEARCH_RADIUS_METERS = 50000  # 50km radius around Miami
MIAMI_COORDS = (25.7617, -80.1918)

# Known service categories and typical price ranges for validation
SERVICE_CATEGORIES = {
    "Injectables": ["Botox", "Dysport", "Xeomin", "Juvederm", "Restylane", "Sculptra", "RHA", "Belotero", "Radiesse"],
    "Body Contouring": ["CoolSculpting", "Emsculpt", "Emsculpt Neo", "truSculpt"],
    "Lasers": ["Fraxel", "CO2", "IPL", "PicoSure", "Morpheus8", "Laser Hair Removal"],
    "Skincare": ["HydraFacial", "Microneedling", "Chemical Peel", "DiamondGlow", "RF Microneedling"],
    "Wellness": ["Semaglutide", "Tirzepatide", "IV Therapy", "IV Vitamin Drip", "NAD+"],
    "Regenerative": ["PRP", "Exosome", "Stem Cell", "PRP Hair", "PRP Facial"]
}

# Price validation ranges (USD) - reject outliers
PRICE_RANGES = {
    "Botox": (8, 25),          # per unit
    "Dysport": (3, 8),         # per unit
    "Xeomin": (10, 15),        # per unit
    "Juvederm": (500, 850),    # per syringe
    "Restylane": (500, 800),   # per syringe
    "Sculptra": (800, 1200),   # per vial
    "CoolSculpting": (500, 1000), # per cycle
    "Emsculpt": (700, 1000),   # per session
    "Fraxel": (1000, 3000),    # per session
    "Morpheus8": (700, 1200),  # per session
    "HydraFacial": (150, 350), # per session
    "Microneedling": (300, 900), # per session
    "Semaglutide": (300, 600), # per month
    "Tirzepatide": (400, 700), # per month
    "PRP": (600, 1000),        # per session
    "Exosome": (1000, 2000),   # per session
}


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def validate_price(service_item: str, price_usd: float) -> bool:
    """Validate price against known ranges."""
    for key, (min_price, max_price) in PRICE_RANGES.items():
        if key.lower() in service_item.lower():
            return min_price <= price_usd <= max_price
    return True  # Allow unknown services


def categorize_service(item_name: str) -> str:
    """Auto-categorize service based on name."""
    item_lower = item_name.lower()
    for category, keywords in SERVICE_CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in item_lower:
                return category
    return "Other"


def upsert_clinic(conn: sqlite3.Connection, clinic_data: Dict) -> int:
    """Insert or update a clinic record. Returns clinic ID."""
    cursor = conn.cursor()
    
    services_json = json.dumps(clinic_data.get("services", []))
    
    cursor.execute("""
        INSERT OR REPLACE INTO clinics 
        (name, city, state, address, phone, website, rating, reviews_count, services_json, ai_visibility_score, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        clinic_data["name"],
        clinic_data.get("city", "Miami"),
        clinic_data.get("state", "FL"),
        clinic_data.get("address", ""),
        clinic_data.get("phone", ""),
        clinic_data.get("website", ""),
        clinic_data.get("rating", 0.0),
        clinic_data.get("reviews_count", 0),
        services_json,
        clinic_data.get("ai_visibility_score", 50)
    ))
    
    # Get the clinic ID
    cursor.execute("SELECT id FROM clinics WHERE name = ?", (clinic_data["name"],))
    row = cursor.fetchone()
    return row["id"] if row else None


def enrich_from_google_places() -> List[Dict]:
    """Fetch clinics from Google Places API (requires API key)."""
    if not GOOGLE_PLACES_API_KEY:
        print("[!] Google Places API key not configured. Skipping.")
        return []
    
    clinics = []
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{MIAMI_COORDS[0]},{MIAMI_COORDS[1]}",
        "radius": SEARCH_RADIUS_METERS,
        "type": "beauty_salon",
        "keyword": "medspa OR aesthetic OR botox OR filler",
        "key": GOOGLE_PLACES_API_KEY
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for place in data.get("results", [])[:20]:  # Limit to top 20
                    # Get detailed info
                    detail_url = "https://maps.googleapis.com/maps/api/place/details/json"
                    detail_params = {
                        "place_id": place["place_id"],
                        "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,price_level",
                        "key": GOOGLE_PLACES_API_KEY
                    }
                    detail_resp = client.get(detail_url, params=detail_params)
                    if detail_resp.status_code == 200:
                        detail = detail_resp.json().get("result", {})
                        clinic = {
                            "name": detail.get("name", ""),
                            "address": detail.get("formatted_address", ""),
                            "phone": detail.get("formatted_phone_number", ""),
                            "website": detail.get("website", ""),
                            "rating": detail.get("rating", 0.0),
                            "reviews_count": detail.get("user_ratings_total", 0),
                            "city": "Miami",
                            "state": "FL",
                            "services": [],  # Would need separate enrichment
                            "ai_visibility_score": 50
                        }
                        clinics.append(clinic)
            else:
                print(f"[!] Google Places API error: {resp.status_code}")
    except Exception as e:
        print(f"[X] Google Places enrichment error: {e}")
    
    return clinics


def enrich_from_yelp() -> List[Dict]:
    """Fetch clinics from Yelp Fusion API (requires API key)."""
    if not YELP_API_KEY:
        print("[!] Yelp API key not configured. Skipping.")
        return []
    
    clinics = []
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "location": "Miami, FL",
        "categories": "medspa,beautysvc,skincare",
        "radius": SEARCH_RADIUS_METERS,
        "limit": 20
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for biz in data.get("businesses", []):
                    clinic = {
                        "name": biz.get("name", ""),
                        "address": ", ".join(biz.get("location", {}).get("display_address", [])),
                        "phone": biz.get("phone", ""),
                        "website": biz.get("url", ""),
                        "rating": biz.get("rating", 0.0),
                        "reviews_count": biz.get("review_count", 0),
                        "city": biz.get("location", {}).get("city", "Miami"),
                        "state": biz.get("location", {}).get("state", "FL"),
                        "services": [],
                        "ai_visibility_score": 50
                    }
                    clinics.append(clinic)
            else:
                print(f"[!] Yelp API error: {resp.status_code}")
    except Exception as e:
        print(f"[X] Yelp enrichment error: {e}")
    
    return clinics


def enrich_from_manual_import(filepath: str) -> List[Dict]:
    """Import clinics from a local JSON or CSV file."""
    clinics = []
    try:
        if filepath.endswith(".json"):
            with open(filepath, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    clinics = data
                elif isinstance(data, dict) and "clinics" in data:
                    clinics = data["clinics"]
        elif filepath.endswith(".csv"):
            import csv
            with open(filepath, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert CSV row to clinic format
                    services = []
                    if row.get("services"):
                        services = json.loads(row["services"])
                    clinic = {
                        "name": row.get("name", ""),
                        "city": row.get("city", "Miami"),
                        "state": row.get("state", "FL"),
                        "address": row.get("address", ""),
                        "phone": row.get("phone", ""),
                        "website": row.get("website", ""),
                        "rating": float(row.get("rating", 0.0)),
                        "reviews_count": int(row.get("reviews_count", 0)),
                        "services": services,
                        "ai_visibility_score": int(row.get("ai_visibility_score", 50))
                    }
                    clinics.append(clinic)
        print(f"[+] Imported {len(clinics)} clinics from {filepath}")
    except Exception as e:
        print(f"[X] Manual import error: {e}")
    return clinics


def scrape_clinic_website(url: str) -> List[Dict]:
    """Scrape a clinic's website for service pricing (best effort)."""
    services = []
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Generic pricing extraction - look for common patterns
                text = soup.get_text()
                # This is a placeholder - real implementation would be site-specific
                print(f"[+] Scraped {url} - found {len(text)} chars of text")
    except Exception as e:
        print(f"[!] Scraping error for {url}: {e}")
    return services


def run_enrichment_cycle(import_file: Optional[str] = None) -> Dict:
    """Run a single enrichment cycle from all configured sources."""
    conn = get_db_connection()
    stats = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sources_checked": [],
        "clinics_added": 0,
        "clinics_updated": 0,
        "errors": []
    }
    
    all_new_clinics = []
    
    # Source 1: Google Places
    print("\n[*] Checking Google Places API...")
    stats["sources_checked"].append("google_places")
    google_clinics = enrich_from_google_places()
    all_new_clinics.extend(google_clinics)
    print(f"    Found {len(google_clinics)} clinics")
    
    # Source 2: Yelp
    print("\n[*] Checking Yelp Fusion API...")
    stats["sources_checked"].append("yelp")
    yelp_clinics = enrich_from_yelp()
    all_new_clinics.extend(yelp_clinics)
    print(f"    Found {len(yelp_clinics)} clinics")
    
    # Source 3: Manual import file
    if import_file and os.path.exists(import_file):
        print(f"\n[*] Importing from {import_file}...")
        stats["sources_checked"].append(f"manual_import:{import_file}")
        manual_clinics = enrich_from_manual_import(import_file)
        all_new_clinics.extend(manual_clinics)
        print(f"    Imported {len(manual_clinics)} clinics")
    
    # Deduplicate by name
    seen_names = set()
    unique_clinics = []
    for clinic in all_new_clinics:
        name = clinic.get("name", "").strip().lower()
        if name and name not in seen_names:
            seen_names.add(name)
            unique_clinics.append(clinic)
    
    print(f"\n[*] Processing {len(unique_clinics)} unique clinics...")
    
    # Upsert each clinic
    for clinic in unique_clinics:
        if not clinic.get("name"):
            continue
        try:
            # Check if exists
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM clinics WHERE LOWER(name) = LOWER(?)", (clinic["name"],))
            existing = cursor.fetchone()
            
            clinic_id = upsert_clinic(conn, clinic)
            
            if existing:
                stats["clinics_updated"] += 1
                print(f"    [~] Updated: {clinic['name']}")
            else:
                stats["clinics_added"] += 1
                print(f"    [+] Added: {clinic['name']}")
        except Exception as e:
            error_msg = f"Failed to upsert {clinic.get('name', 'unknown')}: {e}"
            stats["errors"].append(error_msg)
            print(f"    [X] {error_msg}")
    
    conn.commit()
    conn.close()
    
    print(f"\n[✓] Enrichment complete. Added: {stats['clinics_added']}, Updated: {stats['clinics_updated']}")
    if stats["errors"]:
        print(f"    Errors: {len(stats['errors'])}")
    
    return stats


def run_daemon(interval_seconds: int = 3600, import_file: Optional[str] = None):
    """Run continuous enrichment daemon."""
    print(f"[*] Starting enrichment daemon (interval: {interval_seconds}s)")
    print(f"[*] Press Ctrl+C to stop")
    
    while True:
        try:
            run_enrichment_cycle(import_file)
            print(f"\n[*] Sleeping for {interval_seconds} seconds...")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n[*] Enrichment daemon stopped.")
            break
        except Exception as e:
            print(f"[X] Daemon error: {e}")
            print(f"[*] Retrying in 60 seconds...")
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="MedSpa Data Refinery - Enrichment Pipeline")
    parser.add_argument("--once", action="store_true", help="Run single enrichment cycle")
    parser.add_argument("--daemon", action="store_true", help="Run continuous daemon")
    parser.add_argument("--interval", type=int, default=3600, help="Daemon interval in seconds (default: 3600 = 1 hour)")
    parser.add_argument("--import-file", type=str, help="Path to JSON/CSV file for manual import")
    
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon(args.interval, args.import_file)
    else:
        run_enrichment_cycle(args.import_file)


if __name__ == "__main__":
    main()