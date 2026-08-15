import sqlite3
import json
import httpx
from bs4 import BeautifulSoup
import os

DB_PATH = "medspa_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            city TEXT,
            state TEXT,
            address TEXT,
            phone TEXT,
            website TEXT,
            rating REAL,
            reviews_count INTEGER,
            services_json TEXT,
            ai_visibility_score INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # High-value structured niche data
    clinics_data = [
        {
            "name": "Elegance Aesthetics & MedSpa",
            "city": "Miami",
            "state": "FL",
            "address": "1200 Brickell Ave, Suite 400, Miami, FL 33131",
            "phone": "+1-305-555-0192",
            "website": "https://elegancemedspamiami.example.com",
            "rating": 4.9,
            "reviews_count": 342,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 14.00, "unit": "unit"},
                {"category": "Injectables", "item": "Juvederm Ultra XC", "price_usd": 650.00, "unit": "syringe"},
                {"category": "Body Contouring", "item": "CoolSculpting Elite", "price_usd": 750.00, "unit": "cycle"},
                {"category": "Wellness", "item": "Semaglutide Weight Loss (Monthly)", "price_usd": 399.00, "unit": "month"},
                {"category": "Lasers", "item": "IPL Photofacial", "price_usd": 350.00, "unit": "session"}
            ],
            "ai_visibility_score": 85
        },
        {
            "name": "South Beach Glow MedSpa",
            "city": "Miami",
            "state": "FL",
            "address": "750 Ocean Drive, Miami Beach, FL 33139",
            "phone": "+1-305-555-0144",
            "website": "https://sobe-glow.example.com",
            "rating": 4.8,
            "reviews_count": 512,
            "services": [
                {"category": "Injectables", "item": "Dysport (per unit)", "price_usd": 5.00, "unit": "unit"},
                {"category": "Injectables", "item": "Restylane Kysse", "price_usd": 700.00, "unit": "syringe"},
                {"category": "Wellness", "item": "Tirzepatide Program (Monthly)", "price_usd": 550.00, "unit": "month"},
                {"category": "Skincare", "item": "HydraFacial Deluxe", "price_usd": 275.00, "unit": "session"}
            ],
            "ai_visibility_score": 42
        },
        {
            "name": "Coral Gables Laser & Skin Institute",
            "city": "Miami",
            "state": "FL",
            "address": "2320 Ponce de Leon Blvd, Coral Gables, FL 33134",
            "phone": "+1-305-555-0188",
            "website": "https://coralgableslaser.example.com",
            "rating": 4.9,
            "reviews_count": 189,
            "services": [
                {"category": "Lasers", "item": "Fraxel Dual Laser", "price_usd": 1200.00, "unit": "session"},
                {"category": "Injectables", "item": "Sculptra Aesthetic", "price_usd": 900.00, "unit": "vial"},
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 16.00, "unit": "unit"},
                {"category": "Regenerative", "item": "PRP Hair Restoration", "price_usd": 850.00, "unit": "session"}
            ],
            "ai_visibility_score": 28
        },
        {
            "name": "Wynwood Aesthetics Studio",
            "city": "Miami",
            "state": "FL",
            "address": "250 NW 24th St, Miami, FL 33127",
            "phone": "+1-305-555-0103",
            "website": "https://wynwoodaesthetics.example.com",
            "rating": 4.7,
            "reviews_count": 276,
            "services": [
                {"category": "Injectables", "item": "Xeomin (per unit)", "price_usd": 12.00, "unit": "unit"},
                {"category": "Skincare", "item": "RF Microneedling (Morphius8)", "price_usd": 850.00, "unit": "session"},
                {"category": "Wellness", "item": "IV Vitamin Drip (NAD+)", "price_usd": 250.00, "unit": "infusion"}
            ],
            "ai_visibility_score": 91
        }
    ]

    for item in clinics_data:
        cursor.execute('''
            INSERT OR REPLACE INTO clinics 
            (name, city, state, address, phone, website, rating, reviews_count, services_json, ai_visibility_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item["name"],
            item["city"],
            item["state"],
            item["address"],
            item["phone"],
            item["website"],
            item["rating"],
            item["reviews_count"],
            json.dumps(item["services"]),
            item["ai_visibility_score"]
        ))

    conn.commit()
    conn.close()
    print(f"✅ Successfully seeded {len(clinics_data)} clinics into {DB_PATH}")

if __name__ == "__main__":
    init_db()
    seed_database()
