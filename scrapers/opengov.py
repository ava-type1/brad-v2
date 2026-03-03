"""OpenGov Procurement API Scraper - covers 20+ FL counties"""
import logging
import json
from scrapers.base import BaseScraper
from config import OPENGOV_PORTALS

logger = logging.getLogger(__name__)

class OpenGovScraper(BaseScraper):
    source_name = "opengov"
    
    API_BASE = "https://procurement.opengov.com/api/public"
    
    def scrape(self):
        logger.info(f"Starting OpenGov scrape ({len(OPENGOV_PORTALS)} portals)")
        
        for name, portal_id in OPENGOV_PORTALS.items():
            try:
                self._scrape_portal(name, portal_id)
            except Exception as e:
                logger.warning(f"OpenGov {name}: {e}")
        
        logger.info(f"OpenGov: {self.total_count} total, {self.new_count} new")
        return self.total_count, self.new_count
    
    def _scrape_portal(self, county_name, portal_id):
        # Try the projects API endpoint
        urls_to_try = [
            f"{self.API_BASE}/projects?portal={portal_id}&status=open&limit=100",
            f"https://procurement.opengov.com/api/public/projects?portalSlug={portal_id}&status=open&limit=100",
            f"https://procurement.opengov.com/api/v1/portals/{portal_id}/projects?status=open",
        ]
        
        for url in urls_to_try:
            try:
                r = self.session.get(url, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    projects = data if isinstance(data, list) else data.get("data", data.get("projects", data.get("results", [])))
                    if isinstance(projects, list):
                        for proj in projects:
                            bid = self._parse_project(proj, county_name, portal_id)
                            if bid:
                                self.save_bid(bid)
                        logger.info(f"  OpenGov {county_name}: {len(projects)} projects")
                        return
                    elif isinstance(data, dict) and "items" in data:
                        for proj in data["items"]:
                            bid = self._parse_project(proj, county_name, portal_id)
                            if bid:
                                self.save_bid(bid)
                        return
            except Exception as e:
                logger.debug(f"  OpenGov {county_name} URL failed: {e}")
                continue
        
        # Try the portal page itself for embedded data
        try:
            r = self.session.get(f"https://procurement.opengov.com/portal/{portal_id}", timeout=20)
            if r.ok:
                import re
                json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', r.text, re.DOTALL)
                if json_match:
                    state = json.loads(json_match.group(1))
                    projects = state.get("projects", {}).get("items", [])
                    for proj in projects:
                        bid = self._parse_project(proj, county_name, portal_id)
                        if bid:
                            self.save_bid(bid)
                    logger.info(f"  OpenGov {county_name}: {len(projects)} from page state")
                    return
        except Exception as e:
            logger.debug(f"  OpenGov {county_name} page scrape: {e}")
        
        logger.debug(f"  OpenGov {county_name}: no data found")
    
    def _parse_project(self, proj, county_name, portal_id):
        try:
            title = proj.get("title", proj.get("name", ""))
            if not title:
                return None
            
            proj_id = str(proj.get("id", proj.get("_id", "")))
            
            return {
                "external_id": f"og_{portal_id}_{proj_id}",
                "title": str(title)[:300],
                "description": str(proj.get("description", proj.get("summary", "")))[:3000],
                "agency": county_name,
                "external_url": proj.get("url", f"https://procurement.opengov.com/portal/{portal_id}/projects/{proj_id}"),
                "city": county_name.replace(" County", "").replace(" City", ""),
                "state": "FL",
                "category": proj.get("category", proj.get("type", "")),
                "due_date": proj.get("closeDate", proj.get("dueDate", proj.get("submissionDeadline", ""))),
                "posted_date": proj.get("publishDate", proj.get("createdAt", proj.get("openDate", ""))),
                "contact_name": proj.get("contactName", proj.get("buyerName", "")),
                "contact_email": proj.get("contactEmail", proj.get("buyerEmail", "")),
                "contact_phone": proj.get("contactPhone", ""),
                "estimated_value": proj.get("estimatedValue", proj.get("budget", None)),
                "raw_json": json.dumps(proj)[:5000],
            }
        except Exception as e:
            logger.debug(f"Parse OpenGov project error: {e}")
            return None
