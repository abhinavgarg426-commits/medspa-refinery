"""
MCP Server: Miami MedSpa Data Refinery
Method 3 — Expert Knowledge Archive as MCP Tool

Exposes the SQLite-backed clinic dataset (medspa_data.db) to LLM agents
via the Model Context Protocol over standard stdio.

Tools:
  1) search_clinics_by_city      — list clinics in a given city
  2) query_treatment_pricing     — price-lookup across all clinics for a treatment
  3) get_ai_visibility_scores    — clinic AI visibility / readiness scores

Run:
    python mcp_server.py
    (MCP clients spawn this as a stdio subprocess; no HTTP port needed)
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent / "medspa_data.db"

# ------------------------------------------------------------------ #
# DB helper
# ------------------------------------------------------------------ #
def query_db(query: str, args: tuple = ()) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def parse_services(row: dict[str, Any]) -> dict[str, Any]:
    """Promote the services_json text column into a structured list."""
    raw = row.pop("services_json", "[]")
    try:
        row["services"] = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        row["services"] = []
    return row


# ------------------------------------------------------------------ #
# MCP server
# ------------------------------------------------------------------ #
mcp = FastMCP("miami-medspa-refinery")


# ---- Tool 1: Search clinics by city ----------------------------- #
@mcp.tool()
def search_clinics_by_city(city: str = "miami") -> str:
    """List all aesthetic / medspa clinics in the given city.

    Returns clinic name, address, phone, website, rating, review count,
    and a structured services array (category, item, price_usd, unit).
    """
    rows = query_db(
        "SELECT * FROM clinics WHERE LOWER(city) = LOWER(?)",
        (city,),
    )
    if not rows:
        return json.dumps(
            {"status": "no_results", "city": city, "message": f"No clinics found in {city}."},
            indent=2,
        )
    clinics = [parse_services(r) for r in rows]
    return json.dumps(
        {"status": "success", "city": city, "count": len(clinics), "clinics": clinics},
        indent=2,
    )


# ---- Tool 2: Query pricing for a specific treatment ------------- #
@mcp.tool()
def query_treatment_pricing(treatment: str) -> str:
    """Search every clinic for a given aesthetic treatment name (case-insensitive
    substring match across service `item` and `category`).

    Returns clinic name + the matching service entries (price + unit) so an
    agent can compare prices across Miami.
    """
    q = f"%{treatment.lower()}%"
    # SQLite LIKE is case-insensitive for ASCII by default, but we normalize both sides
    rows = query_db("SELECT * FROM clinics")
    matches: list[dict[str, Any]] = []
    for r in rows:
        services = json.loads(r.get("services_json", "[]"))
        hit = [
            s for s in services
            if treatment.lower() in s.get("item", "").lower()
            or treatment.lower() in s.get("category", "").lower()
        ]
        if hit:
            clinic = parse_services(dict(r))
            clinic.pop("services", None)          # don't dump the full list twice
            clinic["matching_services"] = hit
            matches.append(clinic)
    return json.dumps(
        {
            "status": "success" if matches else "no_results",
            "query": treatment,
            "matches_count": len(matches),
            "results": matches,
        },
        indent=2,
    )


# ---- Tool 3: Retrieve AI visibility scores ---------------------- #
@mcp.tool()
def get_ai_visibility_scores(city: str | None = None) -> str:
    """Return each clinic's AI visibility / readiness score (0-100).

    Optionally filter by city. A low score (<50) means the clinic's web
    presence is poorly indexed by LLMs — a prime target for the AI
    Readiness Agency (Method 2).
    """
    if city:
        rows = query_db(
            "SELECT name, city, ai_visibility_score, website FROM clinics WHERE LOWER(city) = LOWER(?) ORDER BY ai_visibility_score DESC",
            (city,),
        )
    else:
        rows = query_db(
            "SELECT name, city, ai_visibility_score, website FROM clinics ORDER BY ai_visibility_score DESC"
        )
    if not rows:
        return json.dumps(
            {"status": "no_results", "city": city, "message": "No clinics found."},
            indent=2,
        )
    return json.dumps(
        {
            "status": "success",
            "count": len(rows),
            "scores": rows,
            "legend": "<50 = poor AI visibility (agency upsell target); >=80 = LLM-optimized",
        },
        indent=2,
    )


# ------------------------------------------------------------------ #
# Entrypoint — stdio transport
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    # FastMCP.run() blocks on the stdio transport — no uvicorn / port needed.
    # An MCP client (Claude Desktop, Hermes, etc.) spawns this script and
    # communicates over stdin/stdout per the MCP specification.
    mcp.run(transport="stdio")
