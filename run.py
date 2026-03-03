#!/usr/bin/env python3
"""Brad V2 - Main scraper runner"""
import sys
import os
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("brad-v2")

from core.db import init_db, get_active_bids, get_bid_count
from core.notifier import notify_new_bids
from config import DATA_DIR

def run_scrapers():
    init_db()
    
    results = {}
    scrapers = []
    
    # Import all scrapers
    try:
        from scrapers.sam_gov import SAMGovScraper
        scrapers.append(SAMGovScraper())
    except Exception as e:
        logger.error(f"Failed to load SAM.gov scraper: {e}")
    
    try:
        from scrapers.opengov import OpenGovScraper
        scrapers.append(OpenGovScraper())
    except Exception as e:
        logger.error(f"Failed to load OpenGov scraper: {e}")
    
    try:
        from scrapers.mfmp import MFMPScraper
        scrapers.append(MFMPScraper())
    except Exception as e:
        logger.error(f"Failed to load MFMP scraper: {e}")
    
    try:
        from scrapers.demandstar import DemandStarScraper
        scrapers.append(DemandStarScraper())
    except Exception as e:
        logger.error(f"Failed to load DemandStar scraper: {e}")
    
    try:
        from scrapers.fdot import FDOTScraper
        scrapers.append(FDOTScraper())
    except Exception as e:
        logger.error(f"Failed to load FDOT scraper: {e}")
    
    # Run each scraper
    for scraper in scrapers:
        try:
            total, new = scraper.scrape()
            results[scraper.source_name] = {"total": total, "new": new}
        except Exception as e:
            logger.error(f"Scraper {scraper.source_name} failed: {e}")
            results[scraper.source_name] = {"total": 0, "new": 0, "error": str(e)}
    
    # Export to JSON for dashboard
    export_dashboard_data()
    
    # Send Telegram alerts for new high-relevance bids
    notified = notify_new_bids()
    
    total_bids = get_bid_count()
    logger.info(f"=== Brad V2 Complete ===")
    logger.info(f"Total active bids: {total_bids}")
    logger.info(f"Results: {json.dumps(results, indent=2)}")
    logger.info(f"Notifications sent: {notified}")
    
    return results

def export_dashboard_data():
    """Export bids to JSON for the dashboard"""
    os.makedirs(DATA_DIR, exist_ok=True)
    bids = get_active_bids()
    
    # Clean up for JSON serialization
    export = []
    for bid in bids:
        b = dict(bid)
        # Remove raw_json from export to keep file small
        b.pop("raw_json", None)
        export.append(b)
    
    output = {
        "updated": datetime.utcnow().isoformat(),
        "total": len(export),
        "bids": export,
    }
    
    path = os.path.join(DATA_DIR, "bids.json")
    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    logger.info(f"Exported {len(export)} bids to {path}")

if __name__ == "__main__":
    run_scrapers()
