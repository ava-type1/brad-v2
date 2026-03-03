"""SAM.gov Federal Opportunities Scraper - uses public API (no key needed)"""
import logging
import json
from datetime import datetime, timedelta
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class SAMGovScraper(BaseScraper):
    source_name = "sam_gov"
    
    NAICS = ["238910", "238110", "238120", "237110", "237310", "237990", "562910", "115310"]
    
    SEARCH_TERMS = [
        "site preparation Florida",
        "excavation Florida",
        "demolition Florida", 
        "grading earthwork Florida",
        "drainage Florida",
        "construction Florida clearing",
        "site work Florida",
        "land clearing Florida",
        "construction Georgia",
        "site preparation Georgia",
    ]
    
    def scrape(self):
        logger.info("Starting SAM.gov scrape")
        
        # Strategy 1: Official API with NAICS codes
        self._search_official_api()
        
        # Strategy 2: Public search API with keywords
        self._search_public_api()
        
        logger.info(f"SAM.gov: {self.total_count} total, {self.new_count} new")
        return self.total_count, self.new_count
    
    def _search_official_api(self):
        posted_from = (datetime.now() - timedelta(days=90)).strftime("%m/%d/%Y")
        posted_to = datetime.now().strftime("%m/%d/%Y")
        
        for naics in self.NAICS:
            try:
                params = {
                    "postedFrom": posted_from,
                    "postedTo": posted_to,
                    "limit": 100,
                    "offset": 0,
                    "ptype": "o",
                    "ncode": naics,
                    "state": "FL",
                }
                r = self.session.get(
                    "https://api.sam.gov/opportunities/v2/search",
                    params=params, timeout=30
                )
                if r.status_code == 200:
                    data = r.json()
                    opps = data.get("opportunitiesData", [])
                    for opp in opps:
                        bid = self._parse_v2(opp)
                        if bid:
                            self.save_bid(bid)
                else:
                    logger.debug(f"SAM API {naics}: HTTP {r.status_code}")
            except Exception as e:
                logger.debug(f"SAM API NAICS {naics}: {e}")
        
        # Also search GA
        for naics in self.NAICS[:4]:
            try:
                params = {
                    "postedFrom": posted_from, "postedTo": posted_to,
                    "limit": 100, "offset": 0, "ptype": "o",
                    "ncode": naics, "state": "GA",
                }
                r = self.session.get("https://api.sam.gov/opportunities/v2/search", params=params, timeout=30)
                if r.ok:
                    for opp in r.json().get("opportunitiesData", []):
                        bid = self._parse_v2(opp)
                        if bid:
                            self.save_bid(bid)
            except Exception as e:
                logger.debug(f"SAM API GA {naics}: {e}")
    
    def _search_public_api(self):
        for term in self.SEARCH_TERMS:
            for page in range(5):  # Up to 5 pages per term
                try:
                    url = f"https://sam.gov/api/prod/sgs/v1/search/"
                    params = {
                        "index": "opp", "q": term, "page": page,
                        "mode": "search", "sort": "-modifiedDate", "is_active": "true"
                    }
                    r = self.session.get(url, params=params, timeout=30)
                    if r.ok:
                        data = r.json()
                        results = data.get("_embedded", {}).get("results", [])
                        if not results:
                            break
                        for res in results:
                            bid = self._parse_public(res)
                            if bid:
                                self.save_bid(bid)
                    else:
                        break
                except Exception as e:
                    logger.debug(f"SAM public search '{term}' p{page}: {e}")
                    break
    
    def _parse_v2(self, opp):
        try:
            title = opp.get("title", "")
            if not title:
                return None
            notice_id = opp.get("noticeId", opp.get("solicitationNumber", ""))
            desc = opp.get("description", "")
            if isinstance(desc, dict):
                desc = desc.get("body", str(desc))
            
            pop = opp.get("placeOfPerformance", {}) or {}
            state_info = pop.get("state", {}) or {}
            city_info = pop.get("city", {}) or {}
            state = state_info.get("code", "FL") if isinstance(state_info, dict) else "FL"
            city = city_info.get("name", "") if isinstance(city_info, dict) else ""
            
            award = opp.get("award", {}) or {}
            amount = award.get("amount") if isinstance(award, dict) else None
            
            return {
                "external_id": notice_id,
                "title": str(title)[:300],
                "description": str(desc)[:2000],
                "agency": opp.get("fullParentPathName", opp.get("organizationName", "")),
                "external_url": f"https://sam.gov/opp/{notice_id}/view" if notice_id else "",
                "city": city, "state": state,
                "naics_codes": ",".join([str(n) for n in opp.get("naicsCode", [])]) if isinstance(opp.get("naicsCode"), list) else str(opp.get("naicsCode", "")),
                "due_date": opp.get("responseDeadLine", ""),
                "posted_date": opp.get("postedDate", ""),
                "estimated_value": float(amount) if amount else None,
                "contact_name": opp.get("pointOfContact", [{}])[0].get("fullName", "") if isinstance(opp.get("pointOfContact"), list) and opp.get("pointOfContact") else "",
                "contact_email": opp.get("pointOfContact", [{}])[0].get("email", "") if isinstance(opp.get("pointOfContact"), list) and opp.get("pointOfContact") else "",
                "contact_phone": opp.get("pointOfContact", [{}])[0].get("phone", "") if isinstance(opp.get("pointOfContact"), list) and opp.get("pointOfContact") else "",
                "raw_json": json.dumps(opp)[:5000],
            }
        except Exception as e:
            logger.debug(f"Parse v2 error: {e}")
            return None
    
    def _parse_public(self, res):
        try:
            title = res.get("title", "")
            if not title:
                return None
            notice_id = res.get("_id", res.get("noticeId", ""))
            
            # Extract description from descriptions array
            desc = ""
            for d in res.get("descriptions", []):
                content = d.get("content", "")
                if content:
                    # Strip HTML tags
                    import re
                    desc = re.sub(r'<[^>]+>', ' ', content)[:2000]
                    break
            
            # Extract location
            pop = res.get("placeOfPerformance", {}) or {}
            state = pop.get("stateCode", "")
            city = pop.get("city", "")
            
            # Filter: only FL and GA within radius
            full_text = f"{title} {desc}".lower()
            if state and state not in ("FL", "GA"):
                # Check if Florida/Georgia mentioned in text
                if "florida" not in full_text and "fl " not in full_text and "georgia" not in full_text:
                    return None
            
            # Extract contact
            pocs = res.get("pointOfContact", []) or []
            contact_name = pocs[0].get("fullName", "") if pocs else ""
            contact_email = pocs[0].get("email", "") if pocs else ""
            contact_phone = pocs[0].get("phone", "") if pocs else ""
            
            return {
                "external_id": f"pub_{notice_id}",
                "title": str(title)[:300],
                "description": desc,
                "agency": res.get("organizationHierarchy", [{}])[-1].get("name", "") if res.get("organizationHierarchy") else res.get("fullParentPathName", ""),
                "external_url": f"https://sam.gov/opp/{notice_id}/view",
                "city": city, "state": state or "FL",
                "due_date": res.get("responseDate", ""),
                "posted_date": res.get("publishDate", ""),
                "contact_name": contact_name,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "raw_json": json.dumps(res)[:5000],
            }
        except Exception as e:
            logger.debug(f"Parse public error: {e}")
            return None
