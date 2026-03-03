"""Base scraper class"""
import requests
import logging
from core.db import upsert_bid
from core.scorer import score_bid
from core.geocode import geocode_city_state, distance_from_fort_white
from config import ALLOWED_STATES, SOUTH_GA_MAX_LAT

logger = logging.getLogger(__name__)

class BaseScraper:
    source_name = "unknown"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        self.new_count = 0
        self.total_count = 0
    
    def scrape(self):
        raise NotImplementedError
    
    def save_bid(self, bid: dict) -> bool:
        """Process and save a bid. Returns True if new."""
        bid["source"] = self.source_name
        bid["id"] = f"{self.source_name}_{bid.get('external_id', '')}"
        
        # Geocode if needed
        if not bid.get("lat") and bid.get("city"):
            lat, lng = geocode_city_state(bid["city"], bid.get("state", "FL"))
            bid["lat"] = lat
            bid["lng"] = lng

        # Calculate distance
        if bid.get("lat") and bid.get("lng"):
            bid["distance_miles"] = distance_from_fort_white(bid["lat"], bid["lng"])

        # Geographic filter — FL and South GA only
        state = (bid.get("state") or "").strip().upper()
        if state and state not in ALLOWED_STATES:
            logger.debug(f"Skipping bid outside allowed states: {state} — {bid.get('title', '')[:60]}")
            return False
        if state == "GA":
            lat = bid.get("lat")
            if lat and lat > SOUTH_GA_MAX_LAT:
                logger.debug(f"Skipping North/Central GA bid (lat {lat:.2f}): {bid.get('title', '')[:60]}")
                return False

        # Score
        bid["relevance_score"] = score_bid(bid)
        bid["is_active"] = 1
        
        is_new = upsert_bid(bid)
        self.total_count += 1
        if is_new:
            self.new_count += 1
        return is_new
