"""Brad V2 Configuration"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "bids.db")
DATA_DIR = os.path.join(BASE_DIR, "dashboard", "data")

# Fort White, FL
LAT = 29.9402
LNG = -82.7129
RADIUS_MILES = 200

# Geographic filter — only Florida and South Georgia
ALLOWED_STATES = {"FL", "GA"}
SOUTH_GA_MAX_LAT = 32.5  # Anything above this is Metro ATL / North GA — skip it

# Telegram notifications for individual bids — disabled per Kam's request
NOTIFICATIONS_ENABLED = False

# Telegram
TELEGRAM_BOT_TOKEN = "8166433961:AAE-Xm475nhcMooL3pH_6lAmK4EdfKNjAXQ"
TELEGRAM_CHAT_ID = "8169497922"

# Cloudflare
CF_API_TOKEN = "0l-OFc_P00fZZG8S13BMQYSELGn5-yQxJRRfaR8Y"
CF_ACCOUNT_ID = "e1610a51bf2727c3ccbac32d08639d47"

# NAICS codes
NAICS_CODES = ["238910", "238110", "238120", "237110", "237310", "237990", "562910", "115310"]

# Keywords for relevance scoring
POSITIVE_KEYWORDS = [
    "site prep", "site preparation", "grading", "earthwork", "excavation",
    "demolition", "land clearing", "clearing and grubbing", "drainage",
    "retention pond", "detention pond", "stormwater", "culvert", "trenching",
    "dirt work", "fill dirt", "backfill", "compaction", "erosion control",
    "debris removal", "road construction", "utility installation", "sewer",
    "water line", "force main", "underground utilities", "concrete",
    "foundation", "house pad", "building pad", "site work", "sitework",
    "tree removal", "brush clearing", "stump removal", "lot clearing",
    "road base", "subgrade", "mass grading", "rough grading", "fine grading",
]

NEGATIVE_KEYWORDS = [
    "janitorial", "software", "IT services", "consulting", "legal",
    "accounting", "audit", "insurance", "marketing", "food service",
    "medical", "healthcare", "office supplies", "furniture", "vehicles",
    "security guard", "staffing", "roofing", "hvac", "plumbing",
    "electrical", "painting", "flooring", "carpentry", "elevator",
    "fire alarm", "telecom", "printing", "landscaping maintenance",
    "lawn care", "mowing", "pest control",
]

# OpenGov portal IDs
OPENGOV_PORTALS = {
    "Alachua County": "alachua-county",
    "Marion County": "marion-county-fl",
    "Putnam County": "putnam-county-fl",
    "Clay County": "clay-county",
    "Citrus County": "citrusfl",
    "Leon County": "leoncounty",
    "Volusia County": "volusia",
    "Hernando County": "hernandocounty",
    "Bay County": "baycountyfl",
    "Walton County": "waltoncountyfl",
    "Santa Rosa County": "santarosacounty",
    "Escambia County": "escambiacounty",
    "Brevard County": "brevardcounty",
    "Seminole County": "seminolecountyfl",
    "Lake County": "lakecountyfl",
    "Osceola County": "osceolacountyfl",
    "Pasco County": "pascocountyfl",
    "Hillsborough County": "hillsboroughcounty",
    "Pinellas County": "pinellascounty",
    "Sarasota County": "sarasotacounty",
}
