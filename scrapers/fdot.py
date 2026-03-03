"""FDOT e-Procurement scraper"""
import logging
import json
import re
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class FDOTScraper(BaseScraper):
    source_name = "fdot"
    
    def scrape(self):
        logger.info("Starting FDOT scrape")
        
        # FDOT lettings page
        self._scrape_lettings()
        # FDOT contracts page  
        self._scrape_contracts()
        
        logger.info(f"FDOT: {self.total_count} total, {self.new_count} new")
        return self.total_count, self.new_count
    
    def _scrape_lettings(self):
        """Scrape FDOT lettings/bid solicitations"""
        urls = [
            "https://fdotwp1.dot.state.fl.us/procurement/bids/",
            "https://www.fdot.gov/contracts/procurement",
            "https://fdotwp1.dot.state.fl.us/procurement/api/bids?status=open",
        ]
        for url in urls:
            try:
                r = self.session.get(url, timeout=20)
                if r.ok:
                    if "json" in r.headers.get("content-type", ""):
                        for item in r.json() if isinstance(r.json(), list) else r.json().get("data", []):
                            bid = self._parse(item)
                            if bid:
                                self.save_bid(bid)
                        return
                    else:
                        self._parse_html(r.text)
                        return
            except Exception as e:
                logger.debug(f"FDOT {url}: {e}")
    
    def _scrape_contracts(self):
        try:
            r = self.session.get("https://www.fdot.gov/contracts/bid-lettings", timeout=20)
            if r.ok:
                self._parse_html(r.text)
        except Exception as e:
            logger.debug(f"FDOT contracts: {e}")
    
    def _parse_html(self, html):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Look for bid tables or links
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    title = cells[0].get_text(strip=True)
                    link = cells[0].find("a")
                    href = link.get("href", "") if link else ""
                    if title and len(title) > 10:
                        self.save_bid({
                            "external_id": f"fdot_{hash(title) % 1000000}",
                            "title": title[:300],
                            "description": " | ".join(c.get_text(strip=True) for c in cells),
                            "agency": "Florida DOT",
                            "external_url": href if href.startswith("http") else f"https://www.fdot.gov{href}",
                            "city": "", "state": "FL",
                        })
        except Exception as e:
            logger.debug(f"FDOT HTML parse: {e}")
    
    def _parse(self, item):
        try:
            title = item.get("title", item.get("description", ""))
            if not title:
                return None
            return {
                "external_id": f"fdot_{item.get('id', item.get('contractId', ''))}",
                "title": str(title)[:300],
                "description": str(item.get("description", item.get("scope", "")))[:3000],
                "agency": "Florida DOT",
                "external_url": item.get("url", "https://www.fdot.gov/contracts"),
                "city": item.get("county", item.get("district", "")),
                "state": "FL",
                "due_date": item.get("lettingDate", item.get("dueDate", "")),
                "estimated_value": item.get("estimatedCost", None),
                "raw_json": json.dumps(item)[:5000],
            }
        except:
            return None
