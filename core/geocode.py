"""Geocoding and distance calculations"""
import math
import requests
import time
import logging

logger = logging.getLogger(__name__)

FORT_WHITE_LAT = 29.9402
FORT_WHITE_LNG = -82.7129

# Florida city coordinates cache (avoid API calls for common cities)
FL_CITIES = {
    "jacksonville": (30.3322, -81.6557), "gainesville": (29.6516, -82.3248),
    "ocala": (29.1872, -82.1401), "tallahassee": (30.4383, -84.2807),
    "orlando": (28.5383, -81.3792), "tampa": (27.9506, -82.4572),
    "miami": (25.7617, -80.1918), "fort lauderdale": (26.1224, -80.1373),
    "st. petersburg": (27.7676, -82.6403), "pensacola": (30.4213, -87.2169),
    "panama city": (30.1588, -85.6602), "daytona beach": (29.2108, -81.0228),
    "lakeland": (28.0395, -81.9498), "sarasota": (27.3364, -82.5307),
    "lake city": (30.1897, -82.6393), "fort white": (29.9402, -82.7129),
    "palatka": (29.6486, -81.6376), "green cove springs": (29.9922, -81.6784),
    "starke": (29.9441, -82.1093), "brooksville": (28.5553, -82.3879),
    "inverness": (28.8358, -82.3301), "leesburg": (28.8108, -81.8779),
    "deland": (29.0283, -81.3031), "sanford": (28.8003, -81.2731),
    "kissimmee": (28.2920, -81.4076), "clearwater": (27.9659, -82.8001),
    "valdosta": (30.8327, -83.2785), "savannah": (32.0809, -81.0912),
    "brunswick": (31.1499, -81.4915), "waycross": (31.2135, -82.3540),
    "tifton": (31.4505, -83.5085), "albany": (31.5785, -84.1557),
    "thomasville": (30.8366, -83.9788), "moultrie": (31.1799, -83.7891),
}

def haversine(lat1, lng1, lat2, lng2):
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def distance_from_fort_white(lat, lng):
    if lat and lng:
        return round(haversine(FORT_WHITE_LAT, FORT_WHITE_LNG, lat, lng), 1)
    return None

def geocode_city_state(city, state="FL"):
    """Get coordinates for a city. Uses cache first, then Nominatim."""
    if not city:
        return None, None
    
    key = city.lower().strip()
    if key in FL_CITIES:
        return FL_CITIES[key]
    
    try:
        time.sleep(1.1)  # Nominatim rate limit
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{city}, {state}", "format": "json", "limit": 1},
            headers={"User-Agent": "BradV2-BidAggregator/1.0"},
            timeout=10
        )
        if r.ok and r.json():
            d = r.json()[0]
            lat, lng = float(d["lat"]), float(d["lon"])
            FL_CITIES[key] = (lat, lng)
            return lat, lng
    except Exception as e:
        logger.debug(f"Geocode failed for {city}, {state}: {e}")
    
    return None, None
