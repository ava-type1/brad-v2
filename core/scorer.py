"""Relevance scoring for bids"""
from config import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS

def score_bid(bid: dict) -> int:
    score = 0
    text = f"{bid.get('title', '')} {bid.get('description', '')} {bid.get('category', '')}".lower()
    
    # Keyword matching (+40 max)
    matches = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    if matches >= 3:
        score += 40
    elif matches >= 1:
        score += 25
    
    # Distance scoring (+30 max)
    dist = bid.get("distance_miles")
    if dist is not None:
        if dist < 100:
            score += 30
        elif dist < 200:
            score += 20
        elif dist < 300:
            score += 10
    
    # Active/due date (+10)
    due = bid.get("due_date")
    if due:
        from datetime import datetime
        try:
            due_dt = datetime.fromisoformat(due.replace("Z", "+00:00")) if "T" in str(due) else datetime.strptime(str(due)[:10], "%Y-%m-%d")
            if due_dt > datetime.now():
                score += 10
        except:
            pass
    
    # Negative keywords (-20)
    if any(nk in text for nk in NEGATIVE_KEYWORDS):
        score -= 20
    
    # Has value estimate (+5)
    if bid.get("estimated_value"):
        score += 5
    
    return max(0, min(100, score))
