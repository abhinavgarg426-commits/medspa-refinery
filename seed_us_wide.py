"""
seed_us_wide.py
Mass seed of US-wide venues for Agent Browser Knowledge Graph.
Generates 100,000+ realistic venues across 50 US cities, 12+ categories.
"""

import sqlite3
import json
import random
from datetime import datetime
from faker import Faker

DB_PATH = "universal_local_intel.db"
fake = Faker('en_US')
Faker.seed(42)
random.seed(42)

# ============================================================
# 50 US CITIES with real neighborhoods
# ============================================================
US_CITIES = {
    "New York": {
        "state": "NY",
        "neighborhoods": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Harlem", "Williamsburg", 
                         "SoHo", "Chelsea", "Upper East Side", "Lower East Side", "Midtown",
                         "Greenwich Village", "Tribeca", "DUMBO", "Park Slope"],
        "coords": (40.7128, -74.0060)
    },
    "Los Angeles": {
        "state": "CA",
        "neighborhoods": ["Hollywood", "Beverly Hills", "Santa Monica", "Venice", "DTLA",
                         "West Hollywood", "Silver Lake", "Echo Park", "Pasadena", "Brentwood",
                         "Culver City", "Studio City", "Sherman Oaks", "Encino"],
        "coords": (34.0522, -118.2437)
    },
    "Chicago": {
        "state": "IL",
        "neighborhoods": ["The Loop", "Lincoln Park", "Wicker Park", "Lakeview", "Old Town",
                         "River North", "Gold Coast", "Hyde Park", "Logan Square", "Fulton Market"],
        "coords": (41.8781, -87.6298)
    },
    "Houston": {
        "state": "TX",
        "neighborhoods": ["Downtown", "Midtown", "Montrose", "The Heights", "Rice Village",
                         "Memorial", "Galleria", "Museum District", "Washington Ave"],
        "coords": (29.7604, -95.3698)
    },
    "Phoenix": {
        "state": "AZ",
        "neighborhoods": ["Downtown", "Scottsdale", "Tempe", "Mesa", "Arcadia",
                         "Biltmore", "Ahwatukee", "Sunnyvale", "Camelback East"],
        "coords": (33.4484, -112.0740)
    },
    "Philadelphia": {
        "state": "PA",
        "neighborhoods": ["Center City", "Old City", "Rittenhouse", "University City", "Fishtown",
                         "Northern Liberties", "Manayunk", "Chestnut Hill", "Society Hill"],
        "coords": (39.9526, -75.1652)
    },
    "San Antonio": {
        "state": "TX",
        "neighborhoods": ["Downtown", "Riverwalk", "Pearl District", "Southtown", "Alamo Heights",
                         "Stone Oak", "Medical Center", "King William"],
        "coords": (29.4241, -98.4936)
    },
    "San Diego": {
        "state": "CA",
        "neighborhoods": ["Gaslamp Quarter", "La Jolla", "Pacific Beach", "North Park", "Hillcrest",
                         "Old Town", "Coronado", "Del Mar", "Mission Valley"],
        "coords": (32.7157, -117.1611)
    },
    "Dallas": {
        "state": "TX",
        "neighborhoods": ["Downtown", "Uptown", "Deep Ellum", "Bishop Arts", "Highland Park",
                         "Lakewood", "Oak Lawn", "Lower Greenville"],
        "coords": (32.7767, -96.7970)
    },
    "San Jose": {
        "state": "CA",
        "neighborhoods": ["Downtown", "Santana Row", "Willow Glen", "Los Gatos", "Campbell",
                         "Almaden", "Evergreen", "Berryessa"],
        "coords": (37.3382, -121.8863)
    },
    "Austin": {
        "state": "TX",
        "neighborhoods": ["Downtown", "South Congress", "East Austin", "Rainey Street", "Zilker",
                         "Hyde Park", "Mueller", "Domain", "Bouldin Creek"],
        "coords": (30.2672, -97.7431)
    },
    "Jacksonville": {
        "state": "FL",
        "neighborhoods": ["Downtown", "Riverside", "Avondale", "San Marco", "Beaches",
                         "Mandarin", "Southside", "Jacksonville Beach"],
        "coords": (30.3322, -81.6557)
    },
    "Fort Worth": {
        "state": "TX",
        "neighborhoods": ["Downtown", "Sundance Square", "West 7th", "Near Southside", "TCU",
                         "Arlington Heights", "Cultural District"],
        "coords": (32.7555, -97.3308)
    },
    "Columbus": {
        "state": "OH",
        "neighborhoods": ["Short North", "German Village", "Downtown", "Italian Village", "Victorian Village",
                         "University District", "Grandview", "Worthington"],
        "coords": (39.9612, -82.9988)
    },
    "Charlotte": {
        "state": "NC",
        "neighborhoods": ["Uptown", "South End", "NoDa", "Dilworth", "Plaza Midwood",
                         "Ballantyne", "Elizabeth", "Myers Park"],
        "coords": (35.2271, -80.8431)
    },
    "Indianapolis": {
        "state": "IN",
        "neighborhoods": ["Downtown", "Mass Ave", "Broad Ripple", "Fountain Square", "Irvington",
                         "Carmel", "Fishers", "Castleton"],
        "coords": (39.7684, -86.1581)
    },
    "San Francisco": {
        "state": "CA",
        "neighborhoods": ["Mission", "SoMa", "Castro", "Haight", "Marina",
                         "Pacific Heights", "Nob Hill", "North Beach", "Chinatown", "FiDi"],
        "coords": (37.7749, -122.4194)
    },
    "Seattle": {
        "state": "WA",
        "neighborhoods": ["Downtown", "Capitol Hill", "Ballard", "Fremont", "Queen Anne",
                         "Belltown", "Pioneer Square", "Georgetown", "Wallingford"],
        "coords": (47.6062, -122.3321)
    },
    "Denver": {
        "state": "CO",
        "neighborhoods": ["LoDo", "RiNo", "Cherry Creek", "Capitol Hill", "Highlands",
                         "Washington Park", "Cherry Creek", "Sunnyside", "Berkeley"],
        "coords": (39.7392, -104.9903)
    },
    "Washington": {
        "state": "DC",
        "neighborhoods": ["Georgetown", "Dupont Circle", "Capitol Hill", "Adams Morgan", "Logan Circle",
                         "Foggy Bottom", "U Street", "Navy Yard", "H Street"],
        "coords": (38.9072, -77.0369)
    },
    "Boston": {
        "state": "MA",
        "neighborhoods": ["Back Bay", "Beacon Hill", "Cambridge", "Somerville", "South End",
                         "North End", "Fenway", "Allston", "Brighton", "Brookline"],
        "coords": (42.3601, -71.0589)
    },
    "Nashville": {
        "state": "TN",
        "neighborhoods": ["Downtown", "The Gulch", "East Nashville", "Germantown", "12 South",
                         "Berry Hill", "Music Row", "Midtown"],
        "coords": (36.1627, -86.7816)
    },
    "Portland": {
        "state": "OR",
        "neighborhoods": ["Pearl District", "Hawthorne", "Alberta", "Mississippi", "Division",
                         "Northwest", "Sellwood", "St. Johns", "Buckman"],
        "coords": (45.5152, -122.6784)
    },
    "Las Vegas": {
        "state": "NV",
        "neighborhoods": ["The Strip", "Downtown", "Arts District", "Summerlin", "Henderson",
                         "Spring Valley", "Boulder City"],
        "coords": (36.1699, -115.1398)
    },
    "Detroit": {
        "state": "MI",
        "neighborhoods": ["Downtown", "Midtown", "Corktown", "Eastern Market", "Ferndale",
                         "Royal Oak", "Grosse Pointe", "Hamtramck"],
        "coords": (42.3314, -83.0458)
    },
    "Memphis": {
        "state": "TN",
        "neighborhoods": ["Downtown", "Beale Street", "Overton Square", "Cooper-Young", "Midtown",
                         "East Memphis", "Germantown"],
        "coords": (35.1495, -90.0490)
    },
    "Atlanta": {
        "state": "GA",
        "neighborhoods": ["Midtown", "Buckhead", "Virginia-Highland", "Inman Park", "Old Fourth Ward",
                         "West End", "East Atlanta", "Decatur", "Grant Park"],
        "coords": (33.7490, -84.3880)
    },
    "Miami": {
        "state": "FL",
        "neighborhoods": ["Wynwood", "Brickell", "South Beach", "Coral Gables", "Coconut Grove",
                         "Downtown", "Little Havana", "Edgewater", "Design District"],
        "coords": (25.7617, -80.1918)
    },
    "New Orleans": {
        "state": "LA",
        "neighborhoods": ["French Quarter", "Garden District", "Marigny", "CBD", "Uptown",
                         "Mid-City", "Bywater", "Warehouse District"],
        "coords": (29.9511, -90.0715)
    },
    "Minneapolis": {
        "state": "MN",
        "neighborhoods": ["Downtown", "Uptown", "Northeast", "Linden Hills", "Loring Park",
                         "Longfellow", "Powderhorn", "St. Paul"],
        "coords": (44.9778, -93.2650)
    },
    "Pittsburgh": {
        "state": "PA",
        "neighborhoods": ["Downtown", "Strip District", "Lawrenceville", "Shadyside", "South Side",
                         "Oakland", "Bloomfield", "Mt. Washington"],
        "coords": (40.4406, -79.9959)
    },
    "Cleveland": {
        "state": "OH",
        "neighborhoods": ["Downtown", "Ohio City", "Tremont", "University Circle", "Shaker Heights",
                         "Lakewood", "Gordon Square"],
        "coords": (41.4993, -81.6944)
    },
    "Cincinnati": {
        "state": "OH",
        "neighborhoods": ["Downtown", "Over-the-Rhine", "Mt. Adams", "Hyde Park", "Oakley",
                         "Covington", "Newport"],
        "coords": (39.1031, -84.5120)
    },
    "Kansas City": {
        "state": "MO",
        "neighborhoods": ["Downtown", "Crossroads", "Westport", "Plaza", "River Market",
                         "Brookside", "Prairie Village", "Overland Park"],
        "coords": (39.0997, -94.5786)
    },
    "St. Louis": {
        "state": "MO",
        "neighborhoods": ["Downtown", "Soulard", "The Hill", "Central West End", "Lafayette Square",
                         "Maplewood", "Clayton", "University City"],
        "coords": (38.6270, -90.1994)
    },
    "Salt Lake City": {
        "state": "UT",
        "neighborhoods": ["Downtown", "Sugar House", "The Avenues", "Marmalade", "9th & 9th",
                         "Millcreek", "Cottonwood Heights"],
        "coords": (40.7608, -111.8910)
    },
    "Sacramento": {
        "state": "CA",
        "neighborhoods": ["Downtown", "Midtown", "East Sacramento", "Land Park", "R Street",
                         "Folsom", "Roseville", "Davis"],
        "coords": (38.5816, -121.4944)
    },
    "Tampa": {
        "state": "FL",
        "neighborhoods": ["Downtown", "Ybor City", "Hyde Park", "SoHo", "Channelside",
                         "Westshore", "Carrollwood", "St. Petersburg"],
        "coords": (27.9506, -82.4572)
    },
    "Orlando": {
        "state": "FL",
        "neighborhoods": ["Downtown", "Lake Eola", "Winter Park", "Thornton Park", "College Park",
                         "Mills 50", "Doctor Phillips"],
        "coords": (28.5383, -81.3792)
    },
    "Baltimore": {
        "state": "MD",
        "neighborhoods": ["Inner Harbor", "Fells Point", "Canton", "Federal Hill", "Mt. Vernon",
                         "Hampden", "Pigtown", "Towson"],
        "coords": (39.2904, -76.6122)
    },
    "Milwaukee": {
        "state": "WI",
        "neighborhoods": ["Downtown", "Third Ward", "Walker's Point", "Bay View", "Wauwatosa",
                         "Shorewood", "Brookfield"],
        "coords": (43.0389, -87.9065)
    },
    "Hartford": {
        "state": "CT",
        "neighborhoods": ["Downtown", "West Hartford", "Asylum Hill", "Parkville", "South Green",
                         "Wethersfield", "Glastonbury"],
        "coords": (41.7658, -72.6734)
    },
    "Raleigh": {
        "state": "NC",
        "neighborhoods": ["Downtown", "Glenwood South", "Cameron Village", "Five Points", "North Hills",
                         "Crabtree", "Cary", "Durham"],
        "coords": (35.7796, -78.6382)
    },
    "Buffalo": {
        "state": "NY",
        "neighborhoods": ["Downtown", "Elmwood Village", "Allentown", "North Buffalo", "Williamsville",
                         "Cheektowaga"],
        "coords": (42.8864, -78.8784)
    },
    "Birmingham": {
        "state": "AL",
        "neighborhoods": ["Downtown", "Avondale", "Lakeview", "Highland Park", "Five Points South",
                         "Homewood", "Mountain Brook", "Vestavia"],
        "coords": (33.5186, -86.8104)
    },
    "Richmond": {
        "state": "VA",
        "neighborhoods": ["Downtown", "Fan District", "Carytown", "Scott's Addition", "Church Hill",
                         "Shockoe Bottom", "Short Pump", "Midlothian"],
        "coords": (37.5407, -77.4360)
    },
    "Providence": {
        "state": "RI",
        "neighborhoods": ["Downtown", "Federal Hill", "Thayer Street", "Wickenden", "East Side",
                         "Broadway", "Cranston"],
        "coords": (41.8240, -71.4128)
    },
    "Honolulu": {
        "state": "HI",
        "neighborhoods": ["Waikiki", "Downtown", "Ala Moana", "Kakaako", "Manoa", "Kailua",
                         "Hawaii Kai"],
        "coords": (21.3069, -157.8583)
    },
    "Anchorage": {
        "state": "AK",
        "neighborhoods": ["Downtown", "Midtown", "South Addition", "Mountain View", "Eagle River",
                         "Wasilla"],
        "coords": (61.2181, -149.9003)
    },
    "Albuquerque": {
        "state": "NM",
        "neighborhoods": ["Old Town", "Downtown", "Nob Hill", "Barelas", "North Valley",
                         "Rio Rancho", "Corrales"],
        "coords": (35.0844, -106.6504)
    },
}

# ============================================================
# 12+ CATEGORIES
# ============================================================
CATEGORIES = {
    "cafe": {
        "sub_categories": ["specialty_coffee", "health_cafe", "cafe_bakery", "cuban_cafe", 
                          "italian_cafe", "mediterranean_cafe", "japanese_cafe", "tea_house"],
        "price_levels": ["$", "$$"],
        "name_prefixes": ["Brew", "Bean", "Cup", "Steam", "Roast", "Steam", "Grind", "Sip", "Blend"],
        "name_suffixes": ["Coffee", "Cafe", "Roasters", "House", "Co.", "Bar"],
    },
    "restaurant": {
        "sub_categories": ["italian", "japanese", "french", "mexican", "american", "chinese",
                          "indian", "thai", "korean", "mediterranean", "steakhouse", "seafood",
                          "vegan", "brunch"],
        "price_levels": ["$$", "$$$", "$$$$"],
        "name_prefixes": ["The", "Bistro", "Tavern", "Grill", "Kitchen", "House", "Eatery"],
        "name_suffixes": ["Bistro", "Kitchen", "Grill", "Tavern", "Eatery", "House", "Restaurant"],
    },
    "hotel": {
        "sub_categories": ["luxury", "boutique", "business", "resort", "extended_stay", "mid_range",
                          "hostel", "wellness"],
        "price_levels": ["$$$", "$$$$"],
        "name_prefixes": ["The", "Hotel", "Inn", "Suites", "Residences"],
        "name_suffixes": ["Hotel", "Suites", "Inn", "Resort", "Residences", "Lodge"],
    },
    "medspa": {
        "sub_categories": ["aesthetic_clinic", "laser_clinic", "wellness_medspa", "luxury_medspa",
                          "medical_aesthetics", "day_spa"],
        "price_levels": ["$$$", "$$$$"],
        "name_prefixes": ["Elite", "Premier", "Lux", "Renue", "Glow", "Radiance", "Vitality"],
        "name_suffixes": ["Aesthetics", "MedSpa", "Skin Institute", "Beauty Bar", "Wellness Center"],
    },
    "dentist": {
        "sub_categories": ["general_dentistry", "cosmetic_dentistry", "orthodontics", "pediatric",
                          "oral_surgery", "endodontics"],
        "price_levels": ["$$", "$$$"],
        "name_prefixes": ["Bright", "Smile", "Family", "Elite", "Premier", "Modern", "Advanced"],
        "name_suffixes": ["Dental", "Dentistry", "Family Dental", "Dental Care", "Dental Group"],
    },
    "doctor": {
        "sub_categories": ["general_practice", "family_medicine", "internal_medicine", "pediatrics",
                          "urgent_care", "specialty_clinic"],
        "price_levels": ["$$", "$$$"],
        "name_prefixes": ["Health", "Care", "Family", "Premier", "Advanced", "Modern"],
        "name_suffixes": ["Medical Group", "Health Center", "Medical Associates", "Clinic"],
    },
    "nutritionist": {
        "sub_categories": ["registered_dietitian", "clinical_nutrition", "sports_nutrition",
                          "holistic_nutrition", "weight_management"],
        "price_levels": ["$$", "$$$"],
        "name_prefixes": ["Balance", "Vitality", "NutriLife", "Wellness", "Optimal", "Pure"],
        "name_suffixes": ["Nutrition", "Wellness", "Nutrition Studio", "Health Coaching"],
    },
    "gym": {
        "sub_categories": ["fitness_center", "crossfit", "yoga_studio", "pilates", "martial_arts",
                          "personal_training", "climbing"],
        "price_levels": ["$$", "$$$"],
        "name_prefixes": ["Iron", "Peak", "Power", "Flex", "Core", "Fit", "Pulse"],
        "name_suffixes": ["Fitness", "Gym", "Athletic Club", "Performance Lab", "Studio"],
    },
    "bar": {
        "sub_categories": ["craft_cocktail", "wine_bar", "dive_bar", "sports_bar", "rooftop",
                          "speakeasy", "brewery"],
        "price_levels": ["$$", "$$$"],
        "name_prefixes": ["The", "Velvet", "Copper", "Iron", "Whiskey", "Smoke", "Dark"],
        "name_suffixes": ["Bar", "Lounge", "Pub", "Tavern", "Room", "House"],
    },
    "bakery": {
        "sub_categories": ["artisan_bakery", "pastry_shop", "cupcake_shop", "donut_shop"],
        "price_levels": ["$", "$$"],
        "name_prefixes": ["Sweet", "Golden", "Butter", "Flour", "Hearth", "Crust"],
        "name_suffixes": ["Bakery", "Bakeshop", "Patisserie", "Bread Co."],
    },
    "salon": {
        "sub_categories": ["hair_salon", "nail_salon", "barbershop", "beauty_salon", "spa_salon"],
        "price_levels": ["$$", "$$$"],
        "name_prefixes": ["Style", "Glow", "Chic", "Lux", "Modern", "Classic"],
        "name_suffixes": ["Salon", "Studio", "Hair", "Barbershop", "Beauty Bar"],
    },
    "retail": {
        "sub_categories": ["boutique", "thrift_store", "vintage_shop", "luxury_retail", "specialty_store"],
        "price_levels": ["$", "$$", "$$$"],
        "name_prefixes": ["The", "Urban", "Vintage", "Modern", "Curated", "Local"],
        "name_suffixes": ["Shop", "Boutique", "Store", "Market", "Co."],
    },
    "veterinarian": {
        "sub_categories": ["general_vet", "emergency_vet", "specialty_vet", "animal_hospital"],
        "price_levels": ["$$", "$$$"],
        "name_prefixes": ["Family", "Care", "Premier", "Compassion", "Advanced", "Modern"],
        "name_suffixes": ["Veterinary", "Animal Hospital", "Vet Clinic", "Pet Care"],
    },
    "real_estate": {
        "sub_categories": ["residential_brokerage", "commercial_brokerage", "luxury_brokerage",
                          "property_management"],
        "price_levels": ["$$$", "$$$$"],
        "name_prefixes": ["Premier", "Elite", "Modern", "Urban", "Coastal", "Summit"],
        "name_suffixes": ["Real Estate", "Properties", "Group", "Brokers"],
    },
}

# ============================================================
# OFFERING TEMPLATES BY CATEGORY (extended)
# ============================================================
OFFERINGS = {
    "cafe": [
        ("beverage", "Espresso", "Single shot", 3.50, "shot", ["vegan"]),
        ("beverage", "Latte", "Espresso + steamed milk", 5.50, "cup", ["vegan_option"]),
        ("beverage", "Cold Brew", "18-hour steep", 5.00, "cup", ["vegan"]),
        ("beverage", "Cappuccino", "Espresso + foam", 5.00, "cup", ["vegan_option"]),
        ("beverage", "Matcha Latte", "Ceremonial matcha", 6.50, "cup", ["vegan_option"]),
        ("food", "Croissant", "Butter pastry", 4.00, "piece", ["vegetarian"]),
        ("food", "Avocado Toast", "Sourdough + avocado", 12.00, "slice", ["vegan"]),
    ],
    "restaurant": [
        ("food", "Tasting Menu", "Chef's selection", 95.00, "person", ["reservation_required"]),
        ("food", "Wagyu Steak", "A5 wagyu", 85.00, "portion", []),
        ("food", "Fresh Pasta", "Handmade daily", 24.00, "plate", ["vegetarian_option"]),
        ("food", "Seafood Platter", "Fresh catch", 65.00, "plate", ["seafood"]),
        ("food", "Tasting Tacos", "3 chef's choice", 18.00, "order", ["gluten_free_option"]),
        ("beverage", "Wine Pairing", "Sommelier selection", 55.00, "person", ["alcohol"]),
    ],
    "hotel": [
        ("room", "Standard King", "City view", 249.00, "night", ["refundable", "wifi"]),
        ("room", "Deluxe King", "Premium view", 399.00, "night", ["refundable", "wifi"]),
        ("room", "Suite", "Living + bedroom", 799.00, "night", ["refundable", "wifi", "balcony"]),
        ("service", "Valet Parking", "Per day", 45.00, "day", []),
        ("service", "Resort Fee", "Daily amenity", 35.00, "day", ["mandatory"]),
    ],
    "medspa": [
        ("treatment", "Botox (per unit)", "Neuromodulator", 14.00, "unit", ["consultation_required"]),
        ("treatment", "Juvederm", "HA filler", 650.00, "syringe", ["consultation_required"]),
        ("treatment", "CoolSculpting", "Fat freezing", 750.00, "cycle", ["consultation_required"]),
        ("treatment", "HydraFacial", "Multi-step facial", 250.00, "session", []),
        ("treatment", "Microneedling", "Collagen induction", 400.00, "session", []),
    ],
    "dentist": [
        ("service", "Cleaning", "Routine cleaning", 150.00, "visit", ["insurance_accepted"]),
        ("service", "Whitening", "In-office whitening", 500.00, "session", []),
        ("service", "Crown", "Porcelain crown", 1200.00, "tooth", ["insurance_accepted"]),
        ("service", "Implant", "Single tooth implant", 3500.00, "tooth", []),
        ("service", "Invisalign", "Clear aligners", 5500.00, "treatment", []),
    ],
    "doctor": [
        ("service", "Office Visit", "Standard consultation", 200.00, "visit", ["insurance_accepted"]),
        ("service", "Annual Physical", "Comprehensive exam", 350.00, "visit", ["insurance_accepted"]),
        ("service", "Urgent Care Visit", "Same-day sick visit", 175.00, "visit", ["insurance_accepted"]),
        ("service", "Telemedicine", "Virtual consultation", 100.00, "visit", ["insurance_accepted"]),
    ],
    "nutritionist": [
        ("service", "Initial Consultation", "60-min assessment", 175.00, "session", []),
        ("service", "Follow-up", "30-min check-in", 95.00, "session", []),
        ("service", "Meal Plan", "Custom 4-week plan", 250.00, "plan", []),
        ("service", "Group Session", "1-hour group coaching", 45.00, "person", []),
    ],
    "gym": [
        ("service", "Day Pass", "Single day access", 25.00, "day", []),
        ("service", "Monthly Membership", "Unlimited access", 99.00, "month", ["no_commitment"]),
        ("service", "Personal Training", "1-on-1 session", 75.00, "session", []),
        ("service", "Class Drop-in", "Single class", 22.00, "class", []),
    ],
    "bar": [
        ("beverage", "Craft Cocktail", "House signature", 14.00, "drink", ["alcohol"]),
        ("beverage", "Wine Glass", "House pour", 12.00, "glass", ["alcohol"]),
        ("beverage", "Craft Beer", "Local draft", 8.00, "pint", ["alcohol"]),
        ("food", "Bar Snacks", "Chef's selection", 15.00, "plate", []),
    ],
    "bakery": [
        ("food", "Croissant", "Butter pastry", 4.00, "piece", ["vegetarian"]),
        ("food", "Sourdough Loaf", "Artisan bread", 8.00, "loaf", ["vegan"]),
        ("food", "Cupcake", "Daily flavor", 4.50, "piece", ["vegetarian"]),
        ("food", "Donut", "Glazed yeast", 3.50, "piece", ["vegetarian"]),
    ],
    "salon": [
        ("service", "Haircut", "Wash + cut + style", 75.00, "session", []),
        ("service", "Color", "Full color service", 150.00, "session", []),
        ("service", "Highlights", "Partial highlights", 200.00, "session", []),
        ("service", "Manicure", "Classic manicure", 35.00, "session", []),
        ("service", "Pedicure", "Spa pedicure", 55.00, "session", []),
    ],
    "retail": [
        ("product", "Designer Item", "Premium goods", 250.00, "item", []),
        ("product", "Vintage Find", "Curated vintage", 45.00, "item", []),
        ("product", "Local Goods", "Artisan products", 35.00, "item", []),
    ],
    "veterinarian": [
        ("service", "Wellness Exam", "Annual checkup", 85.00, "visit", []),
        ("service", "Vaccinations", "Core vaccines", 65.00, "visit", []),
        ("service", "Dental Cleaning", "Full dental", 350.00, "procedure", []),
        ("service", "Emergency Visit", "Urgent care", 175.00, "visit", ["after_hours_premium"]),
    ],
    "real_estate": [
        ("service", "Buyer Consultation", "1-hour consultation", 0.00, "session", ["free"]),
        ("service", "Listing Fee", "6% commission", 0.06, "percent", ["commission"]),
        ("service", "Property Management", "Monthly mgmt", 8.00, "percent", ["monthly"]),
    ],
}

SENTIMENT_TAGS = {
    "cafe": ["Great for remote work", "Fast WiFi", "Quiet atmosphere", "Outdoor seating", "Specialty roasts", "Vegan options", "Dog friendly"],
    "restaurant": ["Romantic atmosphere", "Great for groups", "Reservation essential", "Chef's tasting menu", "Wine pairing available", "Vegetarian friendly", "Farm to table"],
    "hotel": ["Beachfront access", "Rooftop pool", "Business center", "Pet friendly", "Spa on site", "Concierge service", "Free breakfast"],
    "medspa": ["Board certified physicians", "Natural results", "Latest technology", "Celebrity clientele", "Minimal downtime", "Financing available", "Private treatment rooms"],
    "dentist": ["Family friendly", "Modern equipment", "Insurance accepted", "Evening appointments", "Emergency available", "Sedation dentistry", "Pediatric specialist"],
    "doctor": ["Same-day appointments", "Telemedicine available", "Insurance accepted", "Board certified", "Multilingual staff", "Walk-ins welcome", "Lab on-site"],
    "nutritionist": ["Personalized plans", "Holistic approach", "Sports specialization", "Weight management", "Plant-based expertise", "Insurance accepted", "Virtual sessions"],
    "gym": ["Modern equipment", "Personal training", "Group classes", "24/7 access", "Clean facilities", "Locker rooms", "Childcare available"],
    "bar": ["Craft cocktails", "Live music", "Outdoor seating", "Late night", "Happy hour", "Wine selection", "Knowledgeable bartenders"],
    "bakery": ["Fresh daily", "Artisan bread", "Custom cakes", "Vegan options", "Gluten-free options", "Local favorite", "Early opening"],
    "salon": ["Experienced stylists", "Modern techniques", "Organic products", "Walk-ins welcome", "Bridal services", "Color specialists", "Late hours"],
    "retail": ["Curated selection", "Local brands", "Personal service", "Online shopping", "Returns easy", "Loyalty program", "Gift wrapping"],
    "veterinarian": ["Compassionate care", "Modern equipment", "Boarding available", "Grooming on-site", "Emergency services", "Pet pharmacy", "Cat friendly"],
    "real_estate": ["Top producer", "Luxury specialist", "First-time buyer focus", "Investment properties", "Virtual tours", "Market expertise", "Bilingual agents"],
}

OPENING_HOURS = {
    "cafe": {"mon": "7:00-20:00", "tue": "7:00-20:00", "wed": "7:00-20:00",
             "thu": "7:00-20:00", "fri": "7:00-21:00", "sat": "8:00-21:00", "sun": "8:00-19:00"},
    "restaurant": {"mon": "17:00-22:00", "tue": "17:00-22:00", "wed": "17:00-22:00",
                  "thu": "17:00-22:00", "fri": "17:00-23:00", "sat": "17:00-23:00", "sun": "17:00-21:00"},
    "hotel": {"mon": "0:00-23:59", "tue": "0:00-23:59", "wed": "0:00-23:59",
             "thu": "0:00-23:59", "fri": "0:00-23:59", "sat": "0:00-23:59", "sun": "0:00-23:59"},
    "medspa": {"mon": "9:00-18:00", "tue": "9:00-18:00", "wed": "9:00-18:00",
              "thu": "9:00-19:00", "fri": "9:00-18:00", "sat": "9:00-16:00", "sun": "Closed"},
    "dentist": {"mon": "8:00-17:00", "tue": "8:00-17:00", "wed": "8:00-17:00",
               "thu": "8:00-17:00", "fri": "8:00-17:00", "sat": "9:00-14:00", "sun": "Closed"},
    "doctor": {"mon": "8:00-18:00", "tue": "8:00-18:00", "wed": "8:00-18:00",
              "thu": "8:00-18:00", "fri": "8:00-18:00", "sat": "9:00-13:00", "sun": "Closed"},
    "nutritionist": {"mon": "9:00-18:00", "tue": "9:00-18:00", "wed": "9:00-18:00",
                    "thu": "9:00-18:00", "fri": "9:00-17:00", "sat": "10:00-14:00", "sun": "Closed"},
    "gym": {"mon": "5:00-23:00", "tue": "5:00-23:00", "wed": "5:00-23:00",
           "thu": "5:00-23:00", "fri": "5:00-23:00", "sat": "7:00-21:00", "sun": "7:00-21:00"},
    "bar": {"mon": "16:00-01:00", "tue": "16:00-01:00", "wed": "16:00-01:00",
           "thu": "16:00-02:00", "fri": "16:00-02:00", "sat": "14:00-02:00", "sun": "14:00-00:00"},
    "bakery": {"mon": "6:00-18:00", "tue": "6:00-18:00", "wed": "6:00-18:00",
              "thu": "6:00-18:00", "fri": "6:00-19:00", "sat": "7:00-19:00", "sun": "7:00-15:00"},
    "salon": {"mon": "9:00-19:00", "tue": "9:00-19:00", "wed": "9:00-19:00",
             "thu": "9:00-19:00", "fri": "9:00-20:00", "sat": "9:00-18:00", "sun": "10:00-17:00"},
    "retail": {"mon": "10:00-20:00", "tue": "10:00-20:00", "wed": "10:00-20:00",
              "thu": "10:00-20:00", "fri": "10:00-21:00", "sat": "10:00-21:00", "sun": "11:00-18:00"},
    "veterinarian": {"mon": "8:00-18:00", "tue": "8:00-18:00", "wed": "8:00-18:00",
                    "thu": "8:00-18:00", "fri": "8:00-18:00", "sat": "9:00-15:00", "sun": "Closed"},
    "real_estate": {"mon": "9:00-19:00", "tue": "9:00-19:00", "wed": "9:00-19:00",
                   "thu": "9:00-19:00", "fri": "9:00-19:00", "sat": "10:00-17:00", "sun": "12:00-16:00"},
}


def generate_venue_name(category: str, city: str) -> tuple:
    """Generate a realistic business name."""
    cat_data = CATEGORIES[category]
    prefix = random.choice(cat_data["name_prefixes"])
    suffix = random.choice(cat_data["name_suffixes"])
    neighborhood_word = random.choice(["Park", "Hill", "Square", "Lane", "Main", "Bay", "Lake", "River", "West", "East"])
    
    patterns = [
        f"{prefix} {suffix}",
        f"The {prefix} {suffix}",
        f"{city} {prefix} {suffix}",
        f"{prefix} & {suffix}",
        f"{prefix} on {neighborhood_word}",
    ]
    name = random.choice(patterns)
    sub_category = random.choice(cat_data["sub_categories"])
    return name, sub_category


def generate_address(city: str, state: str) -> str:
    """Generate realistic US address."""
    number = random.randint(100, 9999)
    streets = ["Main St", "Oak Ave", "Maple Dr", "Park Blvd", "Lake St", "Hill Rd",
               "Broadway", "Market St", "1st Ave", "2nd Ave", "Elm St", "Washington St",
               "Lincoln Ave", "Madison St", "Jefferson Blvd", "Sunset Dr", "Sunrise Ave"]
    street = random.choice(streets)
    zipcode = fake.zipcode()
    return f"{number} {street}, {city}, {state} {zipcode}"


def seed_us_wide(target_total=100000):
    """Seed 100K+ US venues."""
    print(f"\nSeeding US-wide dataset (target: {target_total}+ venues)...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Don't delete existing - we keep Miami data and ADD US-wide
    existing = cursor.execute("SELECT COUNT(*) FROM venues").fetchone()[0]
    print(f"Existing venues: {existing}")
    
    cities = list(US_CITIES.keys())
    venues_per_city = max(50, target_total // len(cities))
    
    total_inserted = 0
    
    for city_name, city_data in US_CITIES.items():
        state = city_data["state"]
        neighborhoods = city_data["neighborhoods"]
        base_lat, base_lng = city_data["coords"]
        
        for category, cat_data in CATEGORIES.items():
            # Each category gets proportional representation
            venues_this_cat = venues_per_city // len(CATEGORIES)
            
            for _ in range(venues_this_cat):
                name, sub_category = generate_venue_name(category, city_name)
                neighborhood = random.choice(neighborhoods)
                
                # Location with offset
                lat = round(base_lat + random.uniform(-0.15, 0.15), 6)
                lng = round(base_lng + random.uniform(-0.15, 0.15), 6)
                address = generate_address(city_name, state)
                
                # Reputation scores
                base_rating = round(random.uniform(3.5, 5.0), 1)
                safety_score = round(min(5.0, base_rating + random.uniform(-0.3, 0.2)), 1)
                value_score = round(min(5.0, base_rating + random.uniform(-0.5, 0.3)), 1)
                ambiance_score = round(min(5.0, base_rating + random.uniform(-0.4, 0.4)), 1)
                service_score = round(min(5.0, base_rating + random.uniform(-0.3, 0.3)), 1)
                reviews_count = random.randint(5, 5000)
                
                # Price level
                price_level = random.choice(cat_data["price_levels"])
                
                # Sentiment tags
                tags_pool = SENTIMENT_TAGS.get(category, ["Great service", "Highly rated"])
                sentiment_tags = json.dumps(random.sample(tags_pool, k=min(4, len(tags_pool))))
                
                # Actionable metadata
                phone = fake.phone_number()
                clean_name = name.lower().replace(' ', '').replace("'", '').replace('&', 'and')
                website = f"https://{clean_name}-{city_name.lower().replace(' ', '')}.example.com"
                booking_url = f"https://booking.example.com/{clean_name}" if category in ["restaurant", "hotel", "salon", "dentist", "doctor", "veterinarian"] else None
                opening_hours = json.dumps(OPENING_HOURS.get(category, OPENING_HOURS["cafe"]))
                
                # Category-specific features
                wifi_speed = random.randint(100, 1000) if category in ["cafe", "hotel"] else None
                outdoor = 1 if category in ["cafe", "restaurant", "hotel", "bar"] and random.random() > 0.4 else 0
                parking = 1 if random.random() > 0.3 else 0
                accessible = 1 if random.random() > 0.15 else 0
                
                cursor.execute("""
                    INSERT INTO venues 
                    (name, category, sub_category, address, city, neighborhood, latitude, longitude,
                     price_level, overall_rating, safety_score, value_score, ambiance_score, service_score,
                     verified_reviews_count, sentiment_tags, phone, website, booking_url, opening_hours,
                     wifi_speed_mbps, has_outdoor_seating, has_parking, is_accessible)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, category, sub_category, address, city_name, neighborhood, lat, lng,
                    price_level, base_rating, safety_score, value_score, ambiance_score, service_score,
                    reviews_count, sentiment_tags, phone, website, booking_url, opening_hours,
                    wifi_speed, outdoor, parking, accessible
                ))
                
                venue_id = cursor.lastrowid
                total_inserted += 1
                
                # Insert offerings
                offerings_template = OFFERINGS.get(category, OFFERINGS["restaurant"])
                num_offerings = random.randint(3, 8)
                for offering in random.sample(offerings_template, k=min(num_offerings, len(offerings_template))):
                    off_cat, item, desc, base_price, unit, tags = offering
                    price_variance = base_price * random.uniform(0.8, 1.4) if base_price > 0 else 0
                    cursor.execute("""
                        INSERT INTO offerings (venue_id, category, item, description, price_usd, unit, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (venue_id, off_cat, item, desc, round(price_variance, 2), unit, json.dumps(tags)))
        
        # Progress
        if total_inserted % 5000 == 0:
            print(f"  ...inserted {total_inserted} venues")
            conn.commit()
    
    conn.commit()
    
    # Final stats
    cursor.execute("SELECT COUNT(*) FROM venues")
    final_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM offerings")
    offerings_count = cursor.fetchone()[0]
    
    print(f"\nDatabase now has:")
    print(f"  Venues: {final_count:,}")
    print(f"  Offerings: {offerings_count:,}")
    
    cursor.execute("SELECT category, COUNT(*) FROM venues GROUP BY category ORDER BY COUNT(*) DESC")
    print("\nBy category:")
    for cat, cnt in cursor.fetchall():
        print(f"  {cat}: {cnt:,}")
    
    cursor.execute("SELECT city, COUNT(*) FROM venues GROUP BY city ORDER BY COUNT(*) DESC LIMIT 10")
    print("\nTop 10 cities:")
    for city, cnt in cursor.fetchall():
        print(f"  {city}: {cnt:,}")
    
    conn.close()
    print(f"\nTotal inserted this run: {total_inserted:,}")


if __name__ == "__main__":
    seed_us_wide(target_total=100000)