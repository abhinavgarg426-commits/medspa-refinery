"""
agent_browser.py
The default search/recommend engine for AI agents.
Universal knowledge graph access via x402 micropayments.

This is the Google-for-Agents primitive: any intent -> ranked, structured, citable answers.
"""

import sqlite3
import json
import re
from typing import List, Dict, Optional, Any
from datetime import datetime

DB_PATH = "universal_local_intel.db"

# ============================================================
# KNOWLEDGE GRAPH TABLES (beyond venues)
# ============================================================

KG_SCHEMA = """
-- Universal entities table (people, products, concepts, places)
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,  -- person, product, concept, organization, place
    canonical_id TEXT UNIQUE,   -- global stable identifier
    aliases TEXT,               -- JSON array of name variants
    attributes TEXT,            -- JSON object of type-specific attributes
    confidence REAL DEFAULT 1.0,
    source_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationships between entities
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    predicate TEXT NOT NULL,    -- 'located_in', 'offers', 'founded_by', 'similar_to'
    object_id INTEGER NOT NULL,
    weight REAL DEFAULT 1.0,
    evidence TEXT,              -- JSON: [{source, snippet, url}]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES entities(id),
    FOREIGN KEY (object_id) REFERENCES entities(id)
);

-- Facts / claims with provenance
CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    predicate TEXT NOT NULL,
    object_value TEXT NOT NULL,  -- literal value
    confidence REAL DEFAULT 1.0,
    sources TEXT,               -- JSON array of source URLs
    last_verified TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES entities(id)
);

-- Query log for analytics / improving ranking
CREATE TABLE IF NOT EXISTS query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT,
    intent_json TEXT,
    results_count INTEGER,
    selected_result_id INTEGER,
    response_time_ms INTEGER,
    payment_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_relations_subject ON relations(subject_id);
CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject_id);
CREATE INDEX IF NOT EXISTS idx_query_log_time ON query_log(created_at);
"""


def init_kg():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for statement in KG_SCHEMA.strip().split(';'):
        if statement.strip():
            cursor.execute(statement)
    conn.commit()
    conn.close()
    print("Knowledge graph schema initialized")


# ============================================================
# INTENT CLASSIFIER - converts natural language to structured query
# ============================================================

INTENT_PATTERNS = {
    "find_venue": {
        "patterns": [
            r"\b(find|search|look for|where|show me)\b.*\b(cafe|restaurant|hotel|medspa|spa|gym|bar|coffee)\b",
            r"\b(best|top|good|near)\b.*\b(cafe|restaurant|hotel|medspa|place)\b",
            r"\b(wynwood|brickell|south beach|coral gables|coconut grove)\b.*\b(cafe|restaurant|hotel)\b"
        ],
        "target_table": "venues"
    },
    "compare_prices": {
        "patterns": [
            r"\b(price|cost|cheap|expensive|afford)\b",
            r"\bhow much\b.*\b(botox|espresso|room|fillers)\b",
            r"\bcompare\b.*\b(prices?|rates?|costs?)\b"
        ],
        "target_table": "offerings"
    },
    "recommend": {
        "patterns": [
            r"\brecommend\b",
            r"\bsuggest\b.*\b(for me|somewhere)\b",
            r"\bwhat.*\bshould i\b"
        ],
        "target_table": "venues"
    },
    "get_facts": {
        "patterns": [
            r"\bwhat is\b",
            r"\bwho is\b",
            r"\btell me about\b",
            r"\binformation about\b"
        ],
        "target_table": "facts"
    }
}


def classify_intent(text: str) -> Dict:
    """Classify user/agent intent from natural language."""
    text_lower = text.lower().strip()
    
    matched_intents = []
    for intent_name, intent_def in INTENT_PATTERNS.items():
        for pattern in intent_def["patterns"]:
            if re.search(pattern, text_lower):
                matched_intents.append({
                    "intent": intent_name,
                    "target_table": intent_def["target_table"],
                    "confidence": 0.8
                })
                break
    
    # Extract category if mentioned
    category = None
    for cat in ["cafe", "restaurant", "hotel", "medspa"]:
        if cat in text_lower:
            category = cat
            break
    
    # Extract neighborhood
    neighborhood = None
    miami_areas = ["wynwood", "brickell", "south beach", "coral gables", "coconut grove",
                   "downtown", "little havana", "edgewater", "design district", "midtown",
                   "aventura", "doral", "key biscayne", "sunny isles", "bal harbour"]
    for area in miami_areas:
        if area in text_lower:
            neighborhood = area
            break
    
    # Extract price level hints
    price_max = None
    if "$$$$" in text or "expensive" in text_lower or "luxury" in text_lower:
        price_max = "$$$$"
    elif "$$$" in text or "mid-range" in text_lower or "moderate" in text_lower:
        price_max = "$$$"
    elif "$$" in text or "affordable" in text_lower or "cheap" in text_lower:
        price_max = "$$"
    elif "$" in text and "very cheap" in text_lower:
        price_max = "$"
    
    # Extract rating requirement
    min_rating = None
    rating_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*star", text_lower)
    if rating_match:
        min_rating = float(rating_match.group(1))
    elif "highly rated" in text_lower or "best" in text_lower:
        min_rating = 4.5
    
    # Extract required features
    features = []
    feature_map = {
        "fast_wifi": ["fast wifi", "good wifi", "wi-fi", "internet"],
        "outdoor_seating": ["outdoor", "outside", "patio", "terrace"],
        "parking": ["parking", "valet"],
        "pet_friendly": ["pet", "dog"],
        "wifi": ["wifi", "wi-fi"],
        "breakfast": ["breakfast"],
        "delivery": ["delivery"],
        "reservation": ["reservation", "book ahead"],
        "vegan": ["vegan", "plant-based"],
        "spa": ["spa", "sauna"]
    }
    for feat, keywords in feature_map.items():
        if any(kw in text_lower for kw in keywords):
            features.append(feat)
    
    return {
        "primary_intent": matched_intents[0]["intent"] if matched_intents else "general_search",
        "all_intents": matched_intents,
        "category": category,
        "neighborhood": neighborhood,
        "price_max": price_max,
        "min_rating": min_rating,
        "required_features": features,
        "raw_query": text
    }


# ============================================================
# SEARCH ENGINE - multi-table, ranked
# ============================================================

def search_venues(intent: Dict, limit: int = 10) -> List[Dict]:
    """Search venues with intent-based filtering and ranking."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Build query
    where_clauses = []
    params = []
    
    if intent.get("category"):
        where_clauses.append("category = ?")
        params.append(intent["category"])
    
    if intent.get("neighborhood"):
        where_clauses.append("LOWER(neighborhood) = ?")
        params.append(intent["neighborhood"].lower())
    
    if intent.get("price_max"):
        # Map price level to ordinal
        price_order = {"$": 1, "$$": 2, "$$$": 3, "$$$$": 4}
        max_level = price_order.get(intent["price_max"], 4)
        where_clauses.append("CASE price_level WHEN '$' THEN 1 WHEN '$$' THEN 2 WHEN '$$$' THEN 3 WHEN '$$$$' THEN 4 END <= ?")
        params.append(max_level)
    
    if intent.get("min_rating"):
        where_clauses.append("overall_rating >= ?")
        params.append(intent["min_rating"])
    
    # Feature-based filtering (basic)
    if intent.get("required_features"):
        for feat in intent["required_features"]:
            if feat == "outdoor_seating":
                where_clauses.append("has_outdoor_seating = 1")
            elif feat == "parking":
                where_clauses.append("has_parking = 1")
            elif feat == "wifi":
                where_clauses.append("wifi_speed_mbps IS NOT NULL AND wifi_speed_mbps > 0")
    
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    
    # Free-text query - search in name, sub_category, sentiment_tags
    raw_query = intent.get("raw_query", "").lower()
    query_terms = [t for t in re.findall(r'\b\w+\b', raw_query) if len(t) > 3]
    if query_terms and not intent.get("category"):
        text_conditions = []
        for term in query_terms[:3]:
            text_conditions.append("(LOWER(name) LIKE ? OR LOWER(sub_category) LIKE ? OR LOWER(sentiment_tags) LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
        if where_sql:
            where_sql += " AND (" + " OR ".join(text_conditions) + ")"
        else:
            where_sql = "WHERE (" + " OR ".join(text_conditions) + ")"
    
    # Ranking: rating + reviews + features
    sql = f"""
        SELECT * FROM venues
        {where_sql}
        ORDER BY 
            overall_rating DESC,
            verified_reviews_count DESC
        LIMIT ?
    """
    params.append(limit)
    
    cursor.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    # Parse JSON fields
    for r in results:
        try:
            r["sentiment_tags"] = json.loads(r.get("sentiment_tags", "[]"))
        except:
            r["sentiment_tags"] = []
        try:
            r["opening_hours"] = json.loads(r.get("opening_hours", "{}"))
        except:
            r["opening_hours"] = {}
    
    # Compute Agent Match Index (0-100)
    for r in results:
        score = 0
        score += (r["overall_rating"] / 5.0) * 40  # Rating contributes 40%
        score += min(r["verified_reviews_count"] / 2000, 1.0) * 20  # Reviews contribute 20%
        score += (r["safety_score"] / 5.0) * 10
        score += (r["service_score"] / 5.0) * 10
        score += (r["value_score"] / 5.0) * 10
        # Bonus for matching features
        if intent.get("required_features"):
            feature_match_count = sum(1 for f in intent["required_features"] if (
                (f == "outdoor_seating" and r.get("has_outdoor_seating")) or
                (f == "parking" and r.get("has_parking")) or
                (f == "wifi" and r.get("wifi_speed_mbps"))
            ))
            score += (feature_match_count / len(intent["required_features"])) * 10
        r["agent_match_index"] = round(score, 1)
        r["_rationale"] = generate_rationale(r, intent)
    
    # Sort by agent match index
    results.sort(key=lambda x: x["agent_match_index"], reverse=True)
    
    conn.close()
    return results


def generate_rationale(venue: Dict, intent: Dict) -> str:
    """Generate human-readable rationale for match."""
    reasons = []
    if venue["overall_rating"] >= 4.7:
        reasons.append(f"highly rated ({venue['overall_rating']}/5)")
    if venue["verified_reviews_count"] > 1000:
        reasons.append(f"trusted by {venue['verified_reviews_count']}+ reviewers")
    if venue.get("safety_score", 0) >= 4.7:
        reasons.append("excellent safety standards")
    if intent.get("required_features"):
        for feat in intent["required_features"]:
            if feat == "outdoor_seating" and venue.get("has_outdoor_seating"):
                reasons.append("has outdoor seating")
            if feat == "wifi" and venue.get("wifi_speed_mbps"):
                reasons.append(f"WiFi: {venue['wifi_speed_mbps']} Mbps")
            if feat == "parking" and venue.get("has_parking"):
                reasons.append("on-site parking")
    if venue.get("sentiment_tags"):
        top_tags = venue["sentiment_tags"][:2]
        reasons.append(f"noted for: {', '.join(top_tags)}")
    return "; ".join(reasons) if reasons else "solid match for your criteria"


# ============================================================
# RECOMMEND ENGINE - intent-based ranking with multi-signal scoring
# ============================================================

def recommend_venues(intent_payload: Dict, limit: int = 5) -> List[Dict]:
    """Process structured intent payload and return ranked recommendations."""
    # Convert payload to intent dict
    intent = {
        "category": intent_payload.get("category"),
        "neighborhood": intent_payload.get("preferred_area"),
        "price_max": intent_payload.get("max_price_level"),
        "required_features": intent_payload.get("required_features", []),
        "min_rating": intent_payload.get("min_rating"),
        "raw_query": intent_payload.get("query", "")
    }
    
    results = search_venues(intent, limit=limit * 2)
    
    # Add rationale, recommendations
    for r in results:
        r["recommendation_confidence"] = r["agent_match_index"] / 100
    
    return results[:limit]


# ============================================================
# PRICING ANALYTICS - cross-venue aggregation
# ============================================================

def pricing_analytics(category: Optional[str] = None) -> Dict:
    """Aggregate pricing across offerings."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    where = ""
    params = []
    if category:
        where = "WHERE v.category = ?"
        params.append(category)
    
    cursor.execute(f"""
        SELECT 
            o.item,
            o.category as offering_category,
            o.unit,
            COUNT(*) as sample_size,
            AVG(o.price_usd) as avg_price,
            MIN(o.price_usd) as min_price,
            MAX(o.price_usd) as max_price,
            GROUP_CONCAT(DISTINCT v.name) as venues_offering
        FROM offerings o
        JOIN venues v ON o.venue_id = v.id
        {where}
        GROUP BY o.item, o.unit
        ORDER BY o.item
    """, params)
    
    rows = cursor.fetchall()
    conn.close()
    
    analytics = []
    for row in rows:
        item, off_cat, unit, n, avg, mn, mx, venues = row
        analytics.append({
            "item": item,
            "offering_category": off_cat,
            "unit": unit,
            "sample_size": n,
            "avg_price_usd": round(avg, 2),
            "min_price_usd": round(mn, 2),
            "max_price_usd": round(mx, 2),
            "price_spread_usd": round(mx - mn, 2),
            "venues_offering_count": len(venues.split(",")) if venues else 0
        })
    
    return {
        "category_filter": category,
        "total_unique_items": len(analytics),
        "data": analytics
    }


if __name__ == "__main__":
    init_kg()
    
    # Test intent classification
    test_queries = [
        "Find me a cafe in Wynwood with fast WiFi and outdoor seating under $$",
        "Show me the best Botox prices in Miami",
        "Recommend a luxury hotel in South Beach",
        "What's the cheapest espresso in Brickell?"
    ]
    
    for q in test_queries:
        print(f"\nQuery: {q}")
        intent = classify_intent(q)
        print(f"  Intent: {intent['primary_intent']}")
        print(f"  Category: {intent.get('category')}")
        print(f"  Neighborhood: {intent.get('neighborhood')}")
        print(f"  Price max: {intent.get('price_max')}")
        print(f"  Features: {intent.get('required_features')}")
        
        if intent.get("category") in ["cafe", "restaurant", "hotel", "medspa"]:
            results = search_venues(intent, limit=3)
            for r in results:
                print(f"  -> {r['name']} ({r['agent_match_index']}/100): {r['_rationale']}")