#!/usr/bin/env python3
"""
Universal Local Intelligence Database Seed Script
Populates SQLite with 200+ Miami-area venues across 4 categories:
- Cafes (50)
- Restaurants (50)
- Hotels (50)
- MedSpas (50)

Schema supports:
- Core attributes: id, name, category, sub_category, address, city, neighborhood, lat, lng, price_level
- Reputation scores: overall_rating, safety_score, value_score, ambiance_score, service_score, verified_reviews_count
- LLM Sentiment Vectors: structured tags array
- Offerings: generic products/services with pricing
- Actionable metadata: booking URLs, phone, hours, WiFi, outdoor seating
"""

import sqlite3
import json
import random
from datetime import datetime

DB_PATH = "universal_local_intel.db"

# ============================================================
# UNIVERSAL SCHEMA
# ============================================================
SCHEMA_SQL = """
-- Core venues table
CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,           -- cafe, restaurant, hotel, medspa
    sub_category TEXT,                -- e.g., 'specialty_coffee', 'italian', 'boutique', 'aesthetic_clinic'
    address TEXT NOT NULL,
    city TEXT NOT NULL DEFAULT 'Miami',
    neighborhood TEXT,                -- Wynwood, Brickell, South Beach, etc.
    latitude REAL,
    longitude REAL,
    price_level TEXT CHECK(price_level IN ('$', '$$', '$$$', '$$$$')),
    
    -- Multi-dimensional reputation scores (1.0-5.0)
    overall_rating REAL DEFAULT 0.0,
    safety_score REAL DEFAULT 0.0,
    value_score REAL DEFAULT 0.0,
    ambiance_score REAL DEFAULT 0.0,
    service_score REAL DEFAULT 0.0,
    verified_reviews_count INTEGER DEFAULT 0,
    
    -- LLM Sentiment Vectors - structured tags for agent reasoning
    sentiment_tags TEXT,              -- JSON array: ["Great for remote work", "Fast WiFi", "Expensive parking"]
    
    -- Actionable metadata
    phone TEXT,
    website TEXT,
    booking_url TEXT,                 -- Direct reservation/booking link
    opening_hours TEXT,               -- JSON: {"mon": "8:00-22:00", ...}
    wifi_speed_mbps INTEGER,          -- For cafes/hotels
    has_outdoor_seating INTEGER DEFAULT 0,  -- Boolean flag
    has_parking INTEGER DEFAULT 0,
    is_accessible INTEGER DEFAULT 0,
    
    -- Agent match index (computed)
    agent_match_index INTEGER DEFAULT 0,  -- 0-100
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generic offerings table (products/services/pricing)
CREATE TABLE IF NOT EXISTS offerings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id INTEGER NOT NULL,
    category TEXT NOT NULL,           -- e.g., 'beverage', 'food', 'room', 'treatment', 'service'
    item TEXT NOT NULL,               -- e.g., 'Espresso', 'Deluxe King Room', 'Botox (per unit)'
    description TEXT,
    price_usd REAL NOT NULL,
    unit TEXT,                        -- 'cup', 'night', 'unit', 'syringe', 'session', 'month'
    tags TEXT,                        -- JSON array: ['vegan', 'gluten-free', 'refundable']
    is_available INTEGER DEFAULT 1,
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_venues_category ON venues(category);
CREATE INDEX IF NOT EXISTS idx_venues_neighborhood ON venues(neighborhood);
CREATE INDEX IF NOT EXISTS idx_venues_price_level ON venues(price_level);
CREATE INDEX IF NOT EXISTS idx_venues_rating ON venues(overall_rating);
CREATE INDEX IF NOT EXISTS idx_offerings_venue ON offerings(venue_id);
CREATE INDEX IF NOT EXISTS idx_offerings_category ON offerings(category);
"""

# ============================================================
# MIAMI NEIGHBORHOODS & COORDINATES
# ============================================================
NEIGHBORHOODS = {
    "Wynwood": (25.8015, -80.1993),
    "Brickell": (25.7617, -80.1918),
    "South Beach": (25.7907, -80.1300),
    "Coconut Grove": (25.7126, -80.2568),
    "Coral Gables": (25.7215, -80.2684),
    "Downtown": (25.7748, -80.1977),
    "Little Havana": (25.7684, -80.2143),
    "Edgewater": (25.7933, -80.1800),
    "Design District": (25.8121, -80.1956),
    "Midtown": (25.8107, -80.1933),
    "Aventura": (25.9565, -80.1392),
    "Doral": (25.8195, -80.3553),
    "Key Biscayne": (25.6882, -80.1619),
    "Sunny Isles Beach": (25.9415, -80.1212),
    "Bal Harbour": (25.8937, -80.1243),
    "Surfside": (25.8781, -80.1186),
    "North Beach": (25.8500, -80.1200),
    "Coral Way": (25.7433, -80.2400),
    "Flagami": (25.7600, -80.2800),
    "Allapattah": (25.8150, -80.2050),
}

# ============================================================
# SENTIMENT TAG POOLS BY CATEGORY
# ============================================================
SENTIMENT_TAGS = {
    "cafe": [
        "Great for remote work", "Fast WiFi", "Quiet atmosphere", "Expensive parking",
        "Outdoor seating", "Dog friendly", "Vegan options", "Specialty roasts",
        "Late night hours", "Power outlets everywhere", "Good for meetings",
        "Rooftop view", "Live music weekends", "Nitro cold brew", "Oat milk default"
    ],
    "restaurant": [
        "Romantic atmosphere", "Great for groups", "Reservation essential", "Pricey but worth it",
        "Outdoor dining", "Chef's tasting menu", "Wine pairing available", "Vegetarian friendly",
        "Late night kitchen", "Private dining rooms", "Celebration favorite", "Michelin mentioned",
        "Farm to table", "Ocean view", "Rooftop dining", "Family style portions"
    ],
    "hotel": [
        "Beachfront access", "Rooftop pool", "Business center", "Expensive parking",
        "Pet friendly", "Spa on site", "Concierge service", "Airport shuttle",
        "Ocean view rooms", "Kitchenette available", "Gym 24/7", "Valet only",
        "Walking distance to nightlife", "Quiet rooms", "Free breakfast", "Resort fee applies"
    ],
    "medspa": [
        "Board certified physicians", "Natural results", "Consultation fee applies", "Package discounts",
        "Latest technology", "Celebrity clientele", "Minimal downtime", "Financing available",
        "Private treatment rooms", "Complimentary consultation", "Membership program", "Gift cards",
        "Weekend appointments", "Virtual consultations", "Multilingual staff", "Insurance not accepted"
    ]
}

# ============================================================
# DATA GENERATORS BY CATEGORY
# ============================================================

CAFE_NAMES = [
    ("Panther Coffee", "specialty_coffee"), ("Vice City Bean", "specialty_coffee"),
    ("Eternity Coffee Roasters", "specialty_coffee"), ("All Day", "cafe_bakery"),
    ("Buddha Green Cafe", "health_cafe"), ("Dr Smood", "health_cafe"),
    ("Pura Vida", "health_cafe"), ("Beaker & Gray", "cafe_bar"),
    ("The Alchemist", "specialty_coffee"), ("Cafe Creme", "french_cafe"),
    ("Boutiki", "specialty_coffee"), ("Tazza Cafe", "italian_cafe"),
    ("Eternity at The Citadel", "specialty_coffee"), ("Mishas Cupcakes", "cafe_bakery"),
    ("Fireman Dereks Bake Shop", "cafe_bakery"), ("Zak the Baker", "cafe_bakery"),
    ("Bianca", "cafe_bakery"), ("Rosetta Bakery", "cafe_bakery"),
    ("Cortadito Coffee House", "cuban_cafe"), ("Islas Canarias", "cuban_cafe"),
    ("La Colada Gourmet", "cuban_cafe"), ("Cafe Versailles", "cuban_cafe"),
    ("El Pub", "cuban_cafe"), ("Enriquetas", "cuban_cafe"),
    ("Kush", "cafe_bar"), ("Beaker & Gray", "cafe_bar"),
    ("The Corner", "cafe_bar"), ("Sweet Melindas", "cafe_bakery"),
    ("Le Chick", "cafe_bakery"), ("Big Pink", "diner_cafe"),
    ("News Cafe", "diner_cafe"), ("Cafe L'Europe", "european_cafe"),
    ("Sprechers", "delicatessen"), ("Milo's", "diner_cafe"),
    ("Blue Collar", "cafe_bakery"), ("Saruya", "japanese_cafe"),
    ("Katsuya", "japanese_cafe"), ("Uchi", "japanese_cafe"),
    ("Mandolin Aegean Bistro", "mediterranean_cafe"), ("Mandolin", "mediterranean_cafe"),
    ("Cafe Avanti", "italian_cafe"), ("Il Gabbiano", "italian_cafe"),
    ("Cibo Wine Bar", "italian_cafe"), ("Osteria del Teatro", "italian_cafe"),
    ("Cecconis", "italian_cafe"), ("Soho House", "members_cafe"),
    ("The Standard Spa", "hotel_cafe"), ("1 Hotel", "hotel_cafe"),
    ("Faena", "hotel_cafe"), ("Biltmore", "hotel_cafe"),
]

RESTAURANT_NAMES = [
    ("KYU", "asian_fusion"), ("Zuma", "japanese"),
    ("Novikov", "asian_fusion"), ("Komodo", "asian_fusion"),
    ("Cote", "korean_bbq"), ("Mandolin Aegean Bistro", "mediterranean"),
    ("LPM Restaurant", "french_mediterranean"), ("Cecconis", "italian"),
    ("Macchialina", "italian"), ("Fililia", "italian"),
    ("Osteria del Teatro", "italian"), ("Il Gabbiano", "italian"),
    ("Cibo Wine Bar", "italian"), ("Sushi Garage", "japanese"),
    ("Zak the Baker", "bakery_cafe"), ("La Mar", "peruvian"),
    ("Cvi.Che 105", "peruvian"), ("Inti", "peruvian"),
    ("Coyo Taco", "mexican"), ("Taquiza", "mexican"),
    ("Bodega Taqueria", "mexican"), ("El Camino", "mexican"),
    ("La Sandwicherie", "sandwiches"), ("Enriquetas", "cuban"),
    ("Versailles", "cuban"), ("La Carreta", "cuban"),
    ("Islas Canarias", "cuban"), ("Sanguich de Miami", "cuban"),
    ("Kush", "american"), ("Big Pink", "american"),
    ("Yardbird", "southern"), ("Red Rooster", "southern"),
    ("The Continental", "american"), ("Barton G", "american"),
    ("Prime 112", "steakhouse"), ("Smith & Wollensky", "steakhouse"),
    ("LT Steak & Seafood", "steakhouse"), ("Edge Steak", "steakhouse"),
    ("Joes Stone Crab", "seafood"), ("Garcias", "seafood"),
    ("Montys", "seafood"), ("Nikki Beach", "beach_club"),
    ("Baoli", "asian_fusion"), ("LIV", "nightclub_restaurant"),
    ("Story", "nightclub_restaurant"), ("E11even", "nightclub_restaurant"),
]

HOTEL_NAMES = [
    ("1 Hotel South Beach", "luxury"), ("Faena Hotel Miami Beach", "luxury"),
    ("The Setai", "luxury"), ("Four Seasons Miami", "luxury"),
    ("Mandarin Oriental", "luxury"), ("St Regis Bal Harbour", "luxury"),
    ("Ritz-Carlton South Beach", "luxury"), ("W South Beach", "luxury"),
    ("Edition Miami Beach", "luxury"), ("Nobu Hotel Miami Beach", "luxury"),
    ("Confidante Miami Beach", "boutique"), ("The Betsy", "boutique"),
    ("The Tides", "boutique"), ("Shelborne South Beach", "boutique"),
    ("Clevelander", "boutique"), ("Essex House", "boutique"),
    ("Gale South Beach", "boutique"), ("Kimpton Surfcomber", "boutique"),
    ("Kimpton Anglers", "boutique"), ("Kimpton EPIC", "boutique"),
    ("East Miami", "modern"), ("SLS Brickell", "modern"),
    ("EAST Miami", "modern"), ("JW Marriott Marquis", "business"),
    ("JW Marriott Turnberry", "resort"), ("Trump National Doral", "resort"),
    ("Fontainebleau", "resort"), ("Eden Roc", "resort"),
    ("Carillon Miami", "wellness"), ("Acqualina", "luxury"),
    ("The Ritz-Carlton Key Biscayne", "luxury"), ("Hilton Bentley", "mid_range"),
    ("Hilton Garden Inn", "mid_range"), ("Hampton Inn", "mid_range"),
    ("Holiday Inn", "mid_range"), ("Courtyard Marriott", "mid_range"),
    ("Residence Inn", "extended_stay"), ("Homewood Suites", "extended_stay"),
    ("Hyatt Place", "mid_range"), ("Hyatt Centric", "modern"),
    ("Aloft", "modern"), ("Moxy", "modern"),
    ("CitizenM", "modern"), ("YOTEL", "modern"),
    ("Freehand Miami", "hostel_boutique"), ("Generator Miami", "hostel"),
    ("The Vagabond", "historic"), ("The Mutiny", "historic"),
    ("Biltmore Hotel", "historic_luxury"), ("The Standard Spa", "wellness"),
    ("1 Hotel", "luxury"), ("Faena", "luxury"),
]

MEDSPA_NAMES = [
    ("Elegance Aesthetics & MedSpa", "aesthetic_clinic"),
    ("South Beach Glow MedSpa", "aesthetic_clinic"),
    ("Coral Gables Laser & Skin Institute", "laser_clinic"),
    ("Wynwood Aesthetics Studio", "aesthetic_clinic"),
    ("Brickell Luxe MedSpa", "aesthetic_clinic"),
    ("Coconut Grove Aesthetic Center", "aesthetic_clinic"),
    ("Doral Beauty & Wellness MedSpa", "wellness_medspa"),
    ("Aventura Luxury Aesthetics", "luxury_medspa"),
    ("Key Biscayne MedSpa", "aesthetic_clinic"),
    ("Sunny Isles Beach Aesthetic Institute", "aesthetic_clinic"),
    ("Downtown Miami MedSpa", "aesthetic_clinic"),
    ("Little Havana Beauty Lab", "aesthetic_clinic"),
    ("Edgewater Aesthetics & Laser", "laser_clinic"),
    ("Pinecrest Medical Aesthetics", "medical_aesthetics"),
    ("Miami Beach Laser & Skin", "laser_clinic"),
    ("Bal Harbour MedSpa", "luxury_medspa"),
    ("Surfside Aesthetics", "aesthetic_clinic"),
    ("North Beach Wellness Spa", "wellness_medspa"),
    ("Design District Aesthetics", "luxury_medspa"),
    ("Midtown MedSpa", "aesthetic_clinic"),
    ("Coral Way Beauty Bar", "aesthetic_clinic"),
    ("Flagami Laser Center", "laser_clinic"),
    ("Allapattah Aesthetics", "aesthetic_clinic"),
    ("Brickell Medical Spa", "medical_aesthetics"),
    ("Coconut Grove Laser Spa", "laser_clinic"),
    ("South Miami Aesthetics", "aesthetic_clinic"),
    ("Kendall MedSpa", "aesthetic_clinic"),
    ("Homestead Beauty Clinic", "aesthetic_clinic"),
    ("Florida City Aesthetics", "aesthetic_clinic"),
    ("Cutler Bay MedSpa", "aesthetic_clinic"),
    ("Palmetto Bay Aesthetics", "aesthetic_clinic"),
    ("Sunny Isles Medical Spa", "medical_aesthetics"),
    ("Golden Beach Wellness", "wellness_medspa"),
    ("Aventura Laser Center", "laser_clinic"),
    ("Hallandale Aesthetics", "aesthetic_clinic"),
    ("Hollywood MedSpa", "aesthetic_clinic"),
    ("Fort Lauderdale Laser", "laser_clinic"),
    ("Boca Raton Aesthetics", "aesthetic_clinic"),
    ("Delray Beach MedSpa", "aesthetic_clinic"),
    ("West Palm Beach Laser", "laser_clinic"),
    ("Jupiter Aesthetics", "aesthetic_clinic"),
    ("Palm Beach Gardens MedSpa", "luxury_medspa"),
    ("Wellington Aesthetics", "aesthetic_clinic"),
    ("Royal Palm Beach MedSpa", "aesthetic_clinic"),
]

# ============================================================
# OFFERING TEMPLATES BY CATEGORY
# ============================================================

CAFE_OFFERINGS = [
    ("beverage", "Espresso", "Single origin espresso shot", 3.50, "shot", ["vegan"]),
    ("beverage", "Cortado", "Espresso with steamed milk", 4.50, "cup", ["vegan_option"]),
    ("beverage", "Cappuccino", "Espresso with foamed milk", 5.00, "cup", ["vegan_option"]),
    ("beverage", "Latte", "Espresso with steamed milk", 5.50, "cup", ["vegan_option"]),
    ("beverage", "Flat White", "Double shot with microfoam", 5.50, "cup", ["vegan_option"]),
    ("beverage", "Cold Brew", "18-hour steeped cold brew", 5.00, "cup", ["vegan"]),
    ("beverage", "Nitro Cold Brew", "Nitrogen-infused cold brew", 6.00, "cup", ["vegan"]),
    ("beverage", "Matcha Latte", "Ceremonial grade matcha", 6.50, "cup", ["vegan_option"]),
    ("beverage", "Chai Latte", "Spiced black tea with milk", 5.50, "cup", ["vegan_option"]),
    ("beverage", "Drip Coffee", "House blend pour over", 3.00, "cup", ["vegan"]),
    ("food", "Croissant", "Classic butter croissant", 4.00, "piece", ["vegetarian"]),
    ("food", "Almond Croissant", "Almond cream filled", 5.00, "piece", ["vegetarian", "nuts"]),
    ("food", "Avocado Toast", "Sourdough with smashed avocado", 12.00, "slice", ["vegan", "gluten_free_option"]),
    ("food", "Breakfast Sandwich", "Egg, cheese, bacon on brioche", 10.00, "piece", []),
    ("food", "Pastry Box", "Assorted daily pastries", 18.00, "box", ["vegetarian"]),
]

RESTAURANT_OFFERINGS = [
    ("food", "Tasting Menu", "Chef's seasonal tasting", 120.00, "person", ["reservation_required"]),
    ("food", "Wagyu Beef", "A5 Japanese wagyu", 85.00, "portion", []),
    ("food", "Fresh Pasta", "Handmade daily", 28.00, "plate", ["vegetarian_option"]),
    ("food", "Seafood Tower", "Oysters, shrimp, crab, lobster", 95.00, "tower", ["seafood"]),
    ("food", "Ceviche", "Daily catch with leche de tigre", 18.00, "portion", ["gluten_free"]),
    ("food", "Tacos (3)", "Corn tortilla, choice of protein", 16.00, "order", ["gluten_free_option"]),
    ("food", "Steak Frites", "Grass-fed ribeye with fries", 42.00, "plate", []),
    ("food", "Roasted Chicken", "Half chicken with herbs", 32.00, "half", []),
    ("food", "Vegetable Plate", "Seasonal roasted vegetables", 22.00, "plate", ["vegan", "gluten_free"]),
    ("beverage", "Wine Pairing", "Sommelier selected", 65.00, "person", ["alcohol"]),
    ("beverage", "Cocktail", "House signature", 16.00, "drink", ["alcohol"]),
    ("beverage", "Sake Flight", "3 premium pours", 28.00, "flight", ["alcohol"]),
]

HOTEL_OFFERINGS = [
    ("room", "Standard King", "City view, king bed", 299.00, "night", ["refundable", "wifi"]),
    ("room", "Deluxe King", "Ocean view, king bed", 449.00, "night", ["refundable", "wifi", "balcony"]),
    ("room", "Ocean Front Suite", "Direct ocean, separate living", 899.00, "night", ["refundable", "wifi", "balcony", "butler"]),
    ("room", "Presidential Suite", "Full floor, panoramic views", 3500.00, "night", ["refundable", "wifi", "balcony", "butler", "private_pool"]),
    ("service", "Valet Parking", "Per day", 45.00, "day", []),
    ("service", "Self Parking", "Per day", 35.00, "day", []),
    ("service", "Resort Fee", "Daily amenity fee", 45.00, "day", ["mandatory"]),
    ("service", "Spa Treatment", "60-min massage", 180.00, "session", ["reservation_required"]),
    ("service", "Pool Cabana", "Full day rental", 350.00, "day", ["reservation_required"]),
    ("food", "Room Service Breakfast", "Continental for two", 65.00, "order", []),
    ("food", "Minibar", "Curated selection", 15.00, "item", []),
]

MEDSPA_OFFERINGS = [
    ("treatment", "Botox (per unit)", "FDA-approved neuromodulator", 14.00, "unit", ["consultation_required"]),
    ("treatment", "Dysport (per unit)", "Alternative neuromodulator", 5.00, "unit", ["consultation_required"]),
    ("treatment", "Xeomin (per unit)", "Pure-form neuromodulator", 12.00, "unit", ["consultation_required"]),
    ("treatment", "Juvederm Ultra XC", "HA lip filler", 650.00, "syringe", ["consultation_required"]),
    ("treatment", "Juvederm Voluma XC", "Cheek filler", 750.00, "syringe", ["consultation_required"]),
    ("treatment", "Juvederm Volbella XC", "Lip filler", 600.00, "syringe", ["consultation_required"]),
    ("treatment", "Restylane Kysse", "Lip filler", 700.00, "syringe", ["consultation_required"]),
    ("treatment", "Restylane Refyne", "Laugh line filler", 620.00, "syringe", ["consultation_required"]),
    ("treatment", "Sculptra Aesthetic", "Collagen stimulator", 900.00, "vial", ["consultation_required", "series_recommended"]),
    ("treatment", "CoolSculpting Elite", "Fat freezing", 750.00, "cycle", ["consultation_required"]),
    ("treatment", "Emsculpt Neo", "Muscle building + fat reduction", 800.00, "session", ["series_recommended"]),
    ("treatment", "Morpheus8", "RF microneedling", 850.00, "session", ["consultation_required", "downtime_3_days"]),
    ("treatment", "HydraFacial Deluxe", "Multi-step facial", 275.00, "session", []),
    ("treatment", "Microneedling with PRP", "Collagen induction", 650.00, "session", ["downtime_2_days"]),
    ("treatment", "PRP Hair Restoration", "Growth factor therapy", 850.00, "session", ["series_recommended"]),
    ("treatment", "Semaglutide Monthly", "GLP-1 weight loss", 399.00, "month", ["medical_clearance"]),
    ("treatment", "Tirzepatide Monthly", "Dual GLP-1/GIP", 550.00, "month", ["medical_clearance"]),
    ("treatment", "IV Therapy (NAD+)", "Cellular energy", 250.00, "infusion", []),
    ("treatment", "Exosome Facial", "Regenerative therapy", 1200.00, "session", ["consultation_required"]),
    ("treatment", "Laser Hair Removal", "Full body package", 1200.00, "package", ["series_required"]),
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for statement in SCHEMA_SQL.strip().split(';'):
        if statement.strip():
            cursor.execute(statement)
    conn.commit()
    conn.close()
    print("Database schema initialized")


def get_random_location(neighborhood):
    """Get lat/lng with small random offset"""
    base_lat, base_lng = NEIGHBORHOODS[neighborhood]
    return (
        round(base_lat + random.uniform(-0.01, 0.01), 6),
        round(base_lng + random.uniform(-0.01, 0.01), 6)
    )


def generate_opening_hours(category):
    """Generate realistic opening hours by category"""
    if category == "cafe":
        return json.dumps({
            "mon": "7:00-20:00", "tue": "7:00-20:00", "wed": "7:00-20:00",
            "thu": "7:00-20:00", "fri": "7:00-21:00", "sat": "8:00-21:00", "sun": "8:00-19:00"
        })
    elif category == "restaurant":
        return json.dumps({
            "mon": "17:00-22:00", "tue": "17:00-22:00", "wed": "17:00-22:00",
            "thu": "17:00-22:00", "fri": "17:00-23:00", "sat": "17:00-23:00", "sun": "17:00-21:00"
        })
    elif category == "hotel":
        return json.dumps({
            "mon": "0:00-23:59", "tue": "0:00-23:59", "wed": "0:00-23:59",
            "thu": "0:00-23:59", "fri": "0:00-23:59", "sat": "0:00-23:59", "sun": "0:00-23:59"
        })
    else:  # medspa
        return json.dumps({
            "mon": "9:00-18:00", "tue": "9:00-18:00", "wed": "9:00-18:00",
            "thu": "9:00-19:00", "fri": "9:00-18:00", "sat": "9:00-16:00", "sun": "Closed"
        })


def seed_category_venues(category, names_list, offerings_template, count):
    """Seed venues for a specific category"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    neighborhoods_list = list(NEIGHBORHOODS.keys())
    price_levels = {"cafe": ["$", "$$"], "restaurant": ["$$", "$$$", "$$$$"], 
                   "hotel": ["$$$", "$$$$"], "medspa": ["$$$", "$$$$"]}
    
    seeded = 0
    for i, (name, sub_cat) in enumerate(names_list[:count]):
        neighborhood = random.choice(neighborhoods_list)
        lat, lng = get_random_location(neighborhood)
        price_level = random.choice(price_levels[category])
        
        # Generate reputation scores (correlated but with variance)
        base_rating = round(random.uniform(3.8, 4.9), 1)
        overall_rating = base_rating
        safety_score = round(min(5.0, base_rating + random.uniform(-0.3, 0.2)), 1)
        value_score = round(min(5.0, base_rating + random.uniform(-0.5, 0.3)), 1)
        ambiance_score = round(min(5.0, base_rating + random.uniform(-0.4, 0.4)), 1)
        service_score = round(min(5.0, base_rating + random.uniform(-0.3, 0.3)), 1)
        reviews_count = random.randint(50, 2000)
        
        # Sentiment tags (pick 3-6)
        tags_pool = SENTIMENT_TAGS.get(category, [])
        sentiment_tags = json.dumps(random.sample(tags_pool, k=random.randint(3, 6)))
        
        # Actionable metadata
        phone = f"+1-305-555-{random.randint(1000, 9999):04d}"
        clean_name = name.lower().replace(' ', '').replace('&', '').replace('.', '').replace("'", '')
        website = f"https://{clean_name}.example.com"
        booking_url = f"https://resy.example.com/{clean_name}" if category in ["restaurant", "hotel"] else None
        opening_hours = generate_opening_hours(category)
        wifi_speed = random.randint(100, 1000) if category in ["cafe", "hotel"] else None
        outdoor = 1 if category in ["cafe", "restaurant", "hotel"] and random.random() > 0.3 else 0
        parking = 1 if random.random() > 0.4 else 0
        accessible = 1 if random.random() > 0.2 else 0
        
        # Street names
        streets = ['Collins Ave', 'Ocean Dr', 'Brickell Ave', 'Biscayne Blvd', 'NW 2nd Ave', 'SW 8th St', 'NE 1st Ave', 'Ponce de Leon Blvd', 'Grand Ave', 'Crandon Blvd']
        address = f"{random.randint(100, 9999)} {random.choice(streets)}, {neighborhood}, FL {random.randint(33101, 33199)}"
        
        # Insert venue
        cursor.execute("""
            INSERT INTO venues 
            (name, category, sub_category, address, city, neighborhood, latitude, longitude, 
             price_level, overall_rating, safety_score, value_score, ambiance_score, service_score,
             verified_reviews_count, sentiment_tags, phone, website, booking_url, opening_hours,
             wifi_speed_mbps, has_outdoor_seating, has_parking, is_accessible)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, category, sub_cat,
            address,
            "Miami", neighborhood, lat, lng,
            price_level, overall_rating, safety_score, value_score, ambiance_score, service_score,
            reviews_count, sentiment_tags, phone, website, booking_url, opening_hours,
            wifi_speed, outdoor, parking, accessible
        ))
        
        venue_id = cursor.lastrowid
        
        # Insert offerings
        num_offerings = random.randint(5, 10)
        for offering in random.sample(offerings_template, k=min(num_offerings, len(offerings_template))):
            cat, item, desc, price, unit, tags = offering
            # Add price variance
            price_variance = price * random.uniform(0.85, 1.25)
            cursor.execute("""
                INSERT INTO offerings (venue_id, category, item, description, price_usd, unit, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (venue_id, cat, item, desc, round(price_variance, 2), unit, json.dumps(tags)))
        
        seeded += 1
    
    conn.commit()
    conn.close()
    print(f"Seeded {seeded} {category} venues")
    return seeded


def seed_universal_database():
    """Seed all categories"""
    print("\nSeeding Universal Local Intelligence Database...")
    
    # Clear existing data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM offerings")
    cursor.execute("DELETE FROM venues")
    conn.commit()
    conn.close()
    
    total = 0
    total += seed_category_venues("cafe", CAFE_NAMES, CAFE_OFFERINGS, 50)
    total += seed_category_venues("restaurant", RESTAURANT_NAMES, RESTAURANT_OFFERINGS, 50)
    total += seed_category_venues("hotel", HOTEL_NAMES, HOTEL_OFFERINGS, 50)
    total += seed_category_venues("medspa", MEDSPA_NAMES, MEDSPA_OFFERINGS, 50)
    
    print(f"\nTotal venues seeded: {total}")
    
    # Verify
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) FROM venues GROUP BY category")
    for cat, cnt in cursor.fetchall():
        cursor.execute("SELECT COUNT(*) FROM offerings WHERE venue_id IN (SELECT id FROM venues WHERE category=?)", (cat,))
        off_cnt = cursor.fetchone()[0]
        print(f"  {cat}: {cnt} venues, {off_cnt} offerings")
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_universal_database()