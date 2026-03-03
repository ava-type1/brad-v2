"""MyFloridaMarketPlace (MFMP) scraper - FL state procurement"""
import logging
import json
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class MFMPScraper(BaseScraper):
    source_name = "mfmp"
    
    SEARCH_TERMS = [
        "site preparation", "excavation", "demolition", "grading",
        "drainage", "clearing", "earthwork", "construction",
        "road", "utility", "concrete", "stormwater",
    ]
    
    def scrape(self):
        logger.info("Starting MFMP scrape")
        
        # Try the Vendor Bid System RSS/API
        self._scrape_vbs()
        
        # Try MFMP search API
        self._scrape_mfmp_api()
        
        logger.info(f"MFMP: {self.total_count} total, {self.new_count} new")
        return self.total_count, self.new_count
    
    def _scrape_vbs(self):
        """Florida Vendor Bid System"""
        try:
            # VBS has a public search
            url = "https://vendor.myfloridamarketplace.com/search/bids"
            params = {
                "status": "open",
                "category": "construction",
                "pageSize": 100,
            }
            r = self.session.get(url, params=params, timeout=30)
            if r.ok and "json" in r.headers.get("content-type", ""):
                data = r.json()
                for item in data.get("results", data.get("bids", [])):
                    bid = self._parse_vbs(item)
                    if bid:
                        self.save_bid(bid)
        except Exception as e:
            logger.debug(f"VBS scrape: {e}")
        
        # Try alternative VBS endpoint
        try:
            url = "https://vendor.myfloridamarketplace.com/api/bids"
            r = self.session.get(url, params={"status": "open", "limit": 200}, timeout=30)
            if r.ok:
                for item in r.json().get("data", r.json() if isinstance(r.json(), list) else []):
                    bid = self._parse_vbs(item)
                    if bid:
                        self.save_bid(bid)
        except Exception as e:
            logger.debug(f"VBS API: {e}")
    
    def _scrape_mfmp_api(self):
        """Try MFMP search endpoints"""
        for term in self.SEARCH_TERMS:
            try:
                urls = [
                    f"https://vendor.myfloridamarketplace.com/api/search?q={term}&status=open",
                    f"https://myfloridamarketplace.com/api/opportunities?search={term}",
                ]
                for url in urls:
                    r = self.session.get(url, timeout=20)
                    if r.ok and "json" in r.headers.get("content-type", ""):
                        data = r.json()
                        items = data if isinstance(data, list) else data.get("results", data.get("data", []))
                        for item in items:
                            bid = self._parse_vbs(item)
                            if bid:
                                self.save_bid(bid)
                        break
            except Exception as e:
                logger.debug(f"MFMP search '{term}': {e}")
    
    def _parse_vbs(self, item):
        try:
            title = item.get("title", item.get("name", item.get("bidTitle", "")))
            if not title:
                return None
            bid_id = str(item.get("id", item.get("bidId", item.get("solicitation_number", ""))))
            return {
                "external_id": f"mfmp_{bid_id}",
                "title": str(title)[:300],
                "description": str(item.get("description", item.get("scope", "")))[:3000],
                "agency": item.get("agency", item.get("department", item.get("organizationName", "FL State"))),
                "external_url": item.get("url", item.get("link", f"https://vendor.myfloridamarketplace.com/bids/{bid_id}")),
                "city": item.get("city", "Tallahassee"),
                "state": "FL",
                "due_date": item.get("dueDate", item.get("closingDate", item.get("responseDate", ""))),
                "posted_date": item.get("postedDate", item.get("openDate", "")),
                "contact_name": item.get("contactName", item.get("buyerName", "")),
                "contact_email": item.get("contactEmail", item.get("buyerEmail", "")),
                "estimated_value": item.get("estimatedValue", item.get("budget", None)),
                "raw_json": json.dumps(item)[:5000],
            }
        except Exception as e:
            logger.debug(f"Parse MFMP: {e}")
            return None
