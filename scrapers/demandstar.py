"""DemandStar scraper - 50+ FL agencies"""
import logging
import json
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class DemandStarScraper(BaseScraper):
    source_name = "demandstar"
    
    def scrape(self):
        logger.info("Starting DemandStar scrape")
        
        # DemandStar has a public API for active bids
        self._scrape_public_api()
        self._scrape_rss()
        
        logger.info(f"DemandStar: {self.total_count} total, {self.new_count} new")
        return self.total_count, self.new_count
    
    def _scrape_public_api(self):
        """Try DemandStar public endpoints"""
        endpoints = [
            "https://www.demandstar.com/api/bids?state=FL&status=open&category=construction",
            "https://www.demandstar.com/api/v1/opportunities?state=FL&status=active",
            "https://network.demandstar.com/api/bids?state=FL",
        ]
        
        for url in endpoints:
            try:
                r = self.session.get(url, timeout=20)
                if r.ok and "json" in r.headers.get("content-type", ""):
                    data = r.json()
                    items = data if isinstance(data, list) else data.get("results", data.get("bids", data.get("data", [])))
                    for item in items:
                        bid = self._parse(item)
                        if bid:
                            self.save_bid(bid)
                    if items:
                        return
            except Exception as e:
                logger.debug(f"DemandStar endpoint: {e}")
    
    def _scrape_rss(self):
        """Try DemandStar RSS feeds"""
        try:
            r = self.session.get(
                "https://www.demandstar.com/api/rss/bids?state=FL",
                timeout=20
            )
            if r.ok:
                from xml.etree import ElementTree as ET
                root = ET.fromstring(r.text)
                for item in root.findall(".//item"):
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    desc = item.findtext("description", "")
                    pub_date = item.findtext("pubDate", "")
                    if title:
                        self.save_bid({
                            "external_id": f"ds_{hash(link) % 1000000}",
                            "title": title[:300],
                            "description": desc[:3000],
                            "agency": "DemandStar Agency",
                            "external_url": link,
                            "city": "", "state": "FL",
                            "posted_date": pub_date,
                        })
        except Exception as e:
            logger.debug(f"DemandStar RSS: {e}")
    
    def _parse(self, item):
        try:
            title = item.get("title", item.get("name", ""))
            if not title:
                return None
            bid_id = str(item.get("id", item.get("bidId", "")))
            return {
                "external_id": f"ds_{bid_id}",
                "title": str(title)[:300],
                "description": str(item.get("description", item.get("scope", "")))[:3000],
                "agency": item.get("agency", item.get("organization", "")),
                "external_url": item.get("url", item.get("link", f"https://www.demandstar.com/bids/{bid_id}")),
                "city": item.get("city", ""), "state": item.get("state", "FL"),
                "due_date": item.get("dueDate", item.get("closingDate", "")),
                "posted_date": item.get("postedDate", item.get("publishDate", "")),
                "contact_name": item.get("contactName", ""),
                "contact_email": item.get("contactEmail", ""),
                "estimated_value": item.get("estimatedValue", None),
                "raw_json": json.dumps(item)[:5000],
            }
        except:
            return None
