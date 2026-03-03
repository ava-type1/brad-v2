# Brad V2 — Bid Aggregator Rebuild Plan
*Fort White, FL · 250-300mi radius · Max bids, full content, beautiful dashboard*

---

## The Core Problem We're Solving

Old Brad: scrapes links → user clicks → hits login wall → useless.  
Brad V2: stores everything → dashboard shows full card → user decides to bid, no clicking out.

**North Star:** Every bid card shows — title, agency, location, distance, due date, dollar range, description, contact, category — all inline. Zero clicks to external sites to understand what the job is.

---

## Sources (Prioritized by Volume)

### Tier 1 — API-Based (High Volume, Low Fight)

| Source | Coverage | Notes |
|--------|----------|-------|
| **SAM.gov API** | Federal (nationwide) | Free API key, no scraping needed. NAICS filtering built in. Huge volume. |
| **MyFloridaMarketPlace (MFMP)** | All FL state agencies | Hidden API — use Unbrowse to find it. Covers FDOT, DOH, DEP, etc. |
| **OpenGov** | 15+ FL counties | One API integration = Alachua, Marion, Putnam, Citrus, Levy, Hernando, etc. |
| **DemandStar** | 50+ FL agencies | One API integration = massive coverage. Auth wall = Unbrowse target. |
| **BidNet Direct** | Multi-state | WAF bypass already researched. Worth revisiting with Unbrowse. |
| **Bonfire Portal** | 10+ FL agencies | Modern API, easier to reverse-engineer. |
| **PlanetBids** | FL cities/utilities | Used by several FL municipalities. |

### Tier 2 — State Procurement (Medium Effort, Good Volume)

| Source | Coverage |
|--------|----------|
| **FDOT e-Procurement** | FL road/infrastructure contracts |
| **Florida School Boards** | District construction bids (UF, FSU adjacent) |
| **Water Management Districts** | SJRWMD, SRWMD, SWFWMD, NWFWMD, SFWMD |
| **Georgia Team Marketplace** | Southern GA counties within radius |
| **Georgia DOT** | GA infrastructure within radius |

### Tier 3 — County Direct (Lower Volume, Targeted)

Counties within 250mi not on a shared platform — direct scrape:
- Columbia, Gilchrist, Bradford, Clay, Baker, Union, Suwannee (FL)
- Ware, Lowndes, Thomas, Berrien, Clinch, Camden, Chatham (GA)
- Duval/Jacksonville has its own portal (80mi, high volume city)
- Jacksonville JEA (utility contracts — very relevant for site prep)

### Tier 4 — Construction Platforms (Broad Coverage)

| Source | Notes |
|--------|-------|
| **ConstructConnect** | Aggregator — if they have an API, one call = thousands of bids |
| **Dodge Data** | Paid but massive. Worth exploring a trial key. |
| **iSqFt** | Construction-specific, FL coverage |

---

## NAICS Codes We Target

```
238910 — Site Preparation Contractors (primary)
238110 — Poured Concrete Foundation/Structure
238120 — Structural Steel/Precast Concrete
238910 — Excavation Work
238990 — All Other Specialty Trade Contractors
237110 — Water/Sewer Line Construction
237310 — Highway/Street/Bridge Construction
237990 — Other Heavy/Civil Engineering
115310 — Support Activities for Forestry (land clearing)
562910 — Remediation Services (contaminated site cleanup)
```

---

## Architecture

### Data Model (SQLite → JSON export)

```python
Bid {
  id: str (source + external_id)
  title: str
  agency: str
  source: str (sam_gov | mfmp | opengov | demandstar | ...)
  external_id: str
  external_url: str
  
  # Location
  address: str
  city: str
  state: str
  lat: float
  lng: float
  distance_miles: float  # from Fort White (29.9402, -82.7129)
  
  # Bid details
  description: str        # Full text, stored inline
  category: str
  naics_codes: list[str]
  keywords_matched: list[str]
  
  # Financials
  estimated_value: float | None
  bid_bond_required: bool | None
  
  # Dates
  posted_date: datetime
  due_date: datetime | None
  pre_bid_date: datetime | None
  
  # Contact
  contact_name: str
  contact_email: str
  contact_phone: str
  
  # Meta
  relevance_score: int    # 0-100, keyword + distance scoring
  is_active: bool
  scraped_at: datetime
  raw_json: str           # Full source payload for debugging
}
```

### Relevance Scoring

```python
score = 0
score += 40 if any keyword in [title, description]  # "site prep", "grading", "clearing", "demo", "excavation", "earthwork", "concrete", "drainage", "utilities"
score += 30 if distance < 100 miles
score += 20 if distance < 200 miles  
score += 10 if distance < 300 miles
score += 10 if due_date > today (not expired)
score -= 20 if keywords suggest irrelevant (IT, software, medical supplies, etc.)
```

### Folder Structure

```
brad-v2/
├── scrapers/
│   ├── base.py              # Abstract scraper class
│   ├── sam_gov.py           # SAM.gov API
│   ├── mfmp.py              # MyFloridaMarketPlace
│   ├── opengov.py           # OpenGov unified
│   ├── demandstar.py        # DemandStar unified
│   ├── bidnet.py            # BidNet Direct
│   ├── bonfire.py           # Bonfire portal
│   ├── fdot.py              # FL DOT e-procurement
│   ├── county_direct.py     # Direct county scrapers
│   └── georgia.py           # GA state + county
├── core/
│   ├── db.py                # SQLite operations
│   ├── geocode.py           # Nominatim geocoding + distance
│   ├── scorer.py            # Relevance scoring
│   └── notifier.py          # Telegram alerts
├── dashboard/
│   ├── index.html           # Single-file dashboard
│   ├── export_json.py       # DB → JSON for dashboard
│   └── data/bids.json       # Generated data file
├── research/
│   ├── opengov_api.md       # Unbrowse findings
│   ├── demandstar_api.md    # Unbrowse findings
│   └── mfmp_api.md          # Unbrowse findings
├── run.py                   # Main scraper runner
├── config.py                # Radius, keywords, coords
└── requirements.txt
```

---

## Dashboard Design

**Single HTML file, Cloudflare Pages deploy.**

### Layout
- Top bar: total bids, last updated, active filters
- Filter row: Distance (50/100/200/300mi) | Category | Source | Due date | Min relevance
- Sort: Newest | Closest | Due Soonest | Highest Value
- Search box: keyword filter on title/description

### Bid Card
```
┌─────────────────────────────────────────────────────────┐
│ [FEDERAL]  [SITE PREP]  [HIGH RELEVANCE]    Due: Mar 15 │
│                                                          │
│ Site Grading and Earthwork — Cedar Key Boat Ramp        │
│ Levy County, FL · 47 miles                              │
│                                                          │
│ Estimated: $120,000–$180,000  |  Bond: Required         │
│                                                          │
│ Full concrete work including site grading, drainage      │
│ installation, and parking lot preparation for new boat   │
│ ramp facility. Prevailing wage required. NAICS 238910.  │
│                                                          │
│ Contact: John Smith · jsmith@levycountyfl.gov           │
│          (352) 486-5218                                  │
│                                                          │
│ Posted: Mar 2  |  Source: OpenGov  [View Original ↗]    │
└─────────────────────────────────────────────────────────┘
```

Color coding:
- 🔴 Red border = due within 7 days
- 🟡 Yellow = due within 14 days  
- 🟢 Green = 15+ days out
- ⚫ Gray = expired (show collapsed, can toggle)

---

## Automation

- **Cron:** Twice daily (6 AM + 6 PM ET)
- **New bid alert:** Telegram message when relevance score ≥ 60 + not seen before
- **Alert format:**
  ```
  🏗️ NEW BID — High Relevance
  
  Site Clearing & Grading — Alachua County Recreation Dept
  📍 47 miles | Due: Mar 20 | Est: $85,000
  
  "...clearing and grading of 3.2 acres for new sports complex..."
  
  Contact: Jane Doe · jdoe@alachuacounty.us
  ```

---

## Execution Plan

### Phase 1 — API Discovery (Day 1-2)
Use **Unbrowse skill** to map hidden APIs:
- [ ] OpenGov portal (load any FL county that uses it, capture network)
- [ ] DemandStar (capture auth + bid list + bid detail API calls)
- [ ] MFMP (capture state procurement API)
- [ ] BidNet Direct (find the real API behind the WAF)
- [ ] FDOT e-procurement

Deliverable: `research/*.md` files with exact API endpoints, headers, auth tokens.

### Phase 2 — Core Engine (Day 2-4)
- [ ] SQLite schema + db.py
- [ ] Geocoding + distance calculation
- [ ] Relevance scorer
- [ ] SAM.gov scraper (API key first, huge volume immediately)
- [ ] Base scraper class all others inherit from

### Phase 3 — Source Integrations (Day 4-8)
Order by expected volume:
1. SAM.gov (federal, massive)
2. OpenGov (15+ FL counties, one integration)
3. DemandStar (50+ FL agencies, one integration)
4. MFMP (all FL state agencies)
5. BidNet Direct
6. Bonfire
7. County directs (Gilchrist, Clay, Bradford, Columbia, Baker, Union already partially researched)
8. FDOT
9. Georgia sources

### Phase 4 — Dashboard (Day 8-10)
- [ ] export_json.py (DB → flat JSON for dashboard)
- [ ] index.html with bid cards, filters, search
- [ ] Deploy to Cloudflare Pages
- [ ] Test on mobile

### Phase 5 — Alerts + Cron (Day 10-11)
- [ ] Telegram notifier
- [ ] OpenClaw cron job (twice daily)
- [ ] Test full pipeline end to end

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Total bids in DB | 500+ active at any time |
| Sources integrated | 8+ (vs. 5 in old Brad) |
| Bid coverage radius | 300 miles |
| Dashboard load time | < 2 seconds |
| New bid alert lag | < 12 hours from posting |
| Relevant bids visible without clicking out | 100% |

---

## Notes

- SAM.gov API key: free at sam.gov/content/data-services — get this first, instant volume
- Unbrowse runs locally on VPS port 6969 (pm2 managed)
- Dashboard data file updated on each scrape run — Cloudflare Pages redeploys on git push
- Fort White coords hardcoded: `LAT=29.9402, LNG=-82.7129`
- All bids stored indefinitely (mark expired, don't delete) — historical value
