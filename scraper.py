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

    # 14 Miami-area MedSpa clinics with real service items, pricing, and visibility metrics
    clinics_data = [
        # --- Original 4 Clinics ---
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
        },
        # --- 10 NEW Clinics ---
        {
            "name": "Brickell Luxe MedSpa",
            "city": "Miami",
            "state": "FL",
            "address": "900 S Miami Ave, Suite 1200, Miami, FL 33130",
            "phone": "+1-305-555-0201",
            "website": "https://brickellluxemedspa.example.com",
            "rating": 4.9,
            "reviews_count": 428,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 15.00, "unit": "unit"},
                {"category": "Injectables", "item": "Juvederm Voluma XC", "price_usd": 750.00, "unit": "syringe"},
                {"category": "Injectables", "item": "Restylane Defyne", "price_usd": 680.00, "unit": "syringe"},
                {"category": "Body Contouring", "item": "Emsculpt Neo", "price_usd": 800.00, "unit": "session"},
                {"category": "Wellness", "item": "Semaglutide Monthly Program", "price_usd": 425.00, "unit": "month"}
            ],
            "ai_visibility_score": 88
        },
        {
            "name": "Coconut Grove Aesthetic Center",
            "city": "Coconut Grove",
            "state": "FL",
            "address": "3015 Grand Ave, Coconut Grove, FL 33133",
            "phone": "+1-305-555-0212",
            "website": "https://coconutgroveaesthetic.example.com",
            "rating": 4.6,
            "reviews_count": 198,
            "services": [
                {"category": "Injectables", "item": "Dysport (per unit)", "price_usd": 5.50, "unit": "unit"},
                {"category": "Injectables", "item": "RHA Collection (per syringe)", "price_usd": 720.00, "unit": "syringe"},
                {"category": "Skincare", "item": "Chemical Peel (VI Peel)", "price_usd": 300.00, "unit": "session"},
                {"category": "Lasers", "item": "Laser Hair Removal (Full Body)", "price_usd": 1200.00, "unit": "package"}
            ],
            "ai_visibility_score": 35
        },
        {
            "name": "Doral Beauty & Wellness MedSpa",
            "city": "Doral",
            "state": "FL",
            "address": "8400 NW 36th St, Suite 200, Doral, FL 33166",
            "phone": "+1-305-555-0223",
            "website": "https://doralbeautywellness.example.com",
            "rating": 4.8,
            "reviews_count": 334,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 13.50, "unit": "unit"},
                {"category": "Injectables", "item": "Juvederm Volbella XC", "price_usd": 600.00, "unit": "syringe"},
                {"category": "Body Contouring", "item": "CoolSculpting Elite (Abdomen)", "price_usd": 700.00, "unit": "cycle"},
                {"category": "Wellness", "item": "Tirzepatide Weight Loss (Monthly)", "price_usd": 480.00, "unit": "month"},
                {"category": "Skincare", "item": "Microneedling with PRP", "price_usd": 650.00, "unit": "session"}
            ],
            "ai_visibility_score": 55
        },
        {
            "name": "Aventura Luxury Aesthetics",
            "city": "Aventura",
            "state": "FL",
            "address": "21000 NE 28th Ave, Suite 100, Aventura, FL 33180",
            "phone": "+1-305-555-0234",
            "website": "https://aventuraluxury.example.com",
            "rating": 4.9,
            "reviews_count": 267,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 16.50, "unit": "unit"},
                {"category": "Injectables", "item": "Sculptra (per vial)", "price_usd": 950.00, "unit": "vial"},
                {"category": "Injectables", "item": "Restylane Lyft", "price_usd": 700.00, "unit": "syringe"},
                {"category": "Lasers", "item": "CO2 Fractional Laser", "price_usd": 2500.00, "unit": "session"},
                {"category": "Regenerative", "item": "Exosome Facial", "price_usd": 1200.00, "unit": "session"}
            ],
            "ai_visibility_score": 79
        },
        {
            "name": "Key Biscayne MedSpa",
            "city": "Key Biscayne",
            "state": "FL",
            "address": "520 Crandon Blvd, Key Biscayne, FL 33149",
            "phone": "+1-305-555-0245",
            "website": "https://keybiscaynemedspa.example.com",
            "rating": 4.7,
            "reviews_count": 143,
            "services": [
                {"category": "Injectables", "item": "Xeomin (per unit)", "price_usd": 13.00, "unit": "unit"},
                {"category": "Injectables", "item": "Belotero Balance", "price_usd": 550.00, "unit": "syringe"},
                {"category": "Skincare", "item": "HydraFacial Signature", "price_usd": 225.00, "unit": "session"},
                {"category": "Wellness", "item": "IV Therapy (Myers Cocktail)", "price_usd": 180.00, "unit": "infusion"}
            ],
            "ai_visibility_score": 22
        },
        {
            "name": "Sunny Isles Beach Aesthetic Institute",
            "city": "Sunny Isles Beach",
            "state": "FL",
            "address": "17900 Collins Ave, Suite 300, Sunny Isles Beach, FL 33160",
            "phone": "+1-305-555-0256",
            "website": "https://sunnyislesaesthetic.example.com",
            "rating": 4.8,
            "reviews_count": 201,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 14.50, "unit": "unit"},
                {"category": "Injectables", "item": "Juvederm Vollure XC", "price_usd": 650.00, "unit": "syringe"},
                {"category": "Body Contouring", "item": "Emsculpt Neo (4 Sessions)", "price_usd": 3000.00, "unit": "package"},
                {"category": "Lasers", "item": "Morpheus8 RF Microneedling", "price_usd": 900.00, "unit": "session"},
                {"category": "Regenerative", "item": "PRP Facial (Vampire Facial)", "price_usd": 700.00, "unit": "session"}
            ],
            "ai_visibility_score": 68
        },
        {
            "name": "Downtown Miami MedSpa",
            "city": "Miami",
            "state": "FL",
            "address": "200 SE 1st St, Suite 500, Miami, FL 33131",
            "phone": "+1-305-555-0267",
            "website": "https://downtownmiamimedspa.example.com",
            "rating": 4.5,
            "reviews_count": 312,
            "services": [
                {"category": "Injectables", "item": "Dysport (per unit)", "price_usd": 4.75, "unit": "unit"},
                {"category": "Injectables", "item": "Restylane Refyne", "price_usd": 620.00, "unit": "syringe"},
                {"category": "Skincare", "item": "DiamondGlow Facial", "price_usd": 250.00, "unit": "session"},
                {"category": "Wellness", "item": "Semaglutide Weight Loss (Monthly)", "price_usd": 375.00, "unit": "month"},
                {"category": "Lasers", "item": "IPL Photofacial", "price_usd": 300.00, "unit": "session"}
            ],
            "ai_visibility_score": 48
        },
        {
            "name": "Little Havana Beauty Lab",
            "city": "Miami",
            "state": "FL",
            "address": "1500 SW 8th St, Miami, FL 33135",
            "phone": "+1-305-555-0278",
            "website": "https://littlehavanabeauty.example.com",
            "rating": 4.6,
            "reviews_count": 167,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 12.00, "unit": "unit"},
                {"category": "Injectables", "item": "Juvederm Ultra Plus XC", "price_usd": 600.00, "unit": "syringe"},
                {"category": "Skincare", "item": "Microneedling (SkinPen)", "price_usd": 400.00, "unit": "session"},
                {"category": "Wellness", "item": "Tirzepatide Monthly", "price_usd": 450.00, "unit": "month"}
            ],
            "ai_visibility_score": 31
        },
        {
            "name": "Edgewater Aesthetics & Laser",
            "city": "Miami",
            "state": "FL",
            "address": "1800 N Bayshore Dr, Miami, FL 33132",
            "phone": "+1-305-555-0289",
            "website": "https://edgewateraesthetics.example.com",
            "rating": 4.7,
            "reviews_count": 234,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 15.00, "unit": "unit"},
                {"category": "Injectables", "item": "Restylane Kysse", "price_usd": 700.00, "unit": "syringe"},
                {"category": "Lasers", "item": "PicoSure Laser Tattoo Removal", "price_usd": 400.00, "unit": "session"},
                {"category": "Body Contouring", "item": "CoolSculpting Elite (Chin)", "price_usd": 600.00, "unit": "cycle"},
                {"category": "Regenerative", "item": "PRP Hair Restoration", "price_usd": 800.00, "unit": "session"}
            ],
            "ai_visibility_score": 72
        },
        {
            "name": "Pinecrest Medical Aesthetics",
            "city": "Pinecrest",
            "state": "FL",
            "address": "9500 S Dixie Hwy, Suite 1200, Pinecrest, FL 33156",
            "phone": "+1-305-555-0290",
            "website": "https://pinecrestmedaesthetics.example.com",
            "rating": 4.9,
            "reviews_count": 189,
            "services": [
                {"category": "Injectables", "item": "Botox (per unit)", "price_usd": 17.00, "unit": "unit"},
                {"category": "Injectables", "item": "Sculptra Aesthetic", "price_usd": 1000.00, "unit": "vial"},
                {"category": "Injectables", "item": "Juvederm Voluma XC", "price_usd": 780.00, "unit": "syringe"},
                {"category": "Lasers", "item": "Fraxel Re:pair", "price_usd": 3000.00, "unit": "session"},
                {"category": "Regenerative", "item": "Exosome Therapy", "price_usd": 1500.00, "unit": "session"}
            ],
            "ai_visibility_score": 81
        }
    ]

    for item in clinics_data:
        cursor.execute(
            """INSERT OR REPLACE INTO clinics 
            (name, city, state, address, phone, website, rating, reviews_count, services_json, ai_visibility_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
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
            )
        )

    conn.commit()
    conn.close()
    print(f"✅ Successfully seeded {len(clinics_data)} clinics into {DB_PATH}")

if __name__ == "__main__":
    init_db()
    seed_database()