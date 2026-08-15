#!/usr/bin/env python3
"""
keep_alive.py
Lightweight health check ping to prevent Render free-tier instance from sleeping.

Run every 14 minutes via cron (Render free tier sleeps after 15 min of inactivity).
Usage: python keep_alive.py

Can also be run as a background daemon: python keep_alive.py --daemon
"""

import httpx
import time
import sys
import os
import argparse
from datetime import datetime

# Configuration
HEALTH_URL = "https://medspa-refinery-api-44xz.onrender.com/health"
INTERVAL_SECONDS = 14 * 60  # 14 minutes

def ping_health() -> bool:
    """Single health check ping."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(HEALTH_URL)
            status = resp.status_code
            if status == 200:
                data = resp.json()
                print(f"[{datetime.utcnow().isoformat()}Z] HEALTH OK: {data}")
                return True
            else:
                print(f"[{datetime.utcnow().isoformat()}Z] HEALTH FAIL: HTTP {status}")
                return False
    except httpx.TimeoutException:
        print(f"[{datetime.utcnow().isoformat()}Z] HEALTH TIMEOUT")
        return False
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}Z] HEALTH ERROR: {type(e).__name__}: {e}")
        return False


def run_once():
    """Run single ping (for cron)."""
    success = ping_health()
    sys.exit(0 if success else 1)


def run_daemon():
    """Run continuous daemon loop."""
    print(f"[*] Keep-alive daemon started. Pinging {HEALTH_URL} every {INTERVAL_SECONDS//60} minutes.")
    print(f"[*] Press Ctrl+C to stop.")
    
    while True:
        try:
            ping_health()
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n[*] Keep-alive daemon stopped.")
            break
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}Z] DAEMON ERROR: {e}")
            time.sleep(60)  # Wait a minute before retry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render keep-alive health ping")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous daemon")
    parser.add_argument("--once", action="store_true", help="Run single ping (default for cron)")
    
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon()
    else:
        run_once()