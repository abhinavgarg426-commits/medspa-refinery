"""
seed_production_lean.py
Lean production DB for Render free tier.
Keeps it under 30MB by stripping unnecessary data and keeping strategic venue selection.
"""

import sqlite3
import random
import json

DB_PATH = "universal_local_intel.db"

def create_lean_production_db():
    """Create a lean version optimized for Render deployment."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Strategy: Keep 1000 venues spread across top cities/categories
    # This gives diversity while staying under 30MB
    TARGET = 1500  # Lean but covers all categories x major cities
    
    # Get top venues per category by rating
    cursor.execute("""
        DELETE FROM venues WHERE id NOT IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY category ORDER BY overall_rating DESC, verified_reviews_count DESC) as rn
                FROM venues
            ) WHERE rn <= ?
        )
    """, (TARGET // 14,))
    
    cursor.execute("DELETE FROM offerings WHERE venue_id NOT IN (SELECT id FROM venues)")
    
    conn.commit()
    
    # Vacuum to reclaim space
    cursor.execute("VACUUM")
    
    # Final stats
    cursor.execute("SELECT COUNT(*) FROM venues")
    v_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM offerings")
    o_count = cursor.fetchone()[0]
    
    print(f"Lean production DB:")
    print(f"  Venues: {v_count:,}")
    print(f"  Offerings: {o_count:,}")
    
    # Verify size
    conn.close()
    
    import os
    size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"  Size: {size_mb:.1f}MB")
    
    return size_mb

if __name__ == "__main__":
    size = create_lean_production_db()
    if size > 50:
        print(f"\nWARNING: DB still {size:.1f}MB - may exceed Render free tier limits")