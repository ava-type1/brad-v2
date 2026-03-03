"""Telegram notification for new high-relevance bids"""
import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from core.db import get_unnotified_bids, mark_notified

logger = logging.getLogger(__name__)

def send_telegram(text):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
        return r.ok
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False

def notify_new_bids():
    bids = get_unnotified_bids(min_relevance=50)
    if not bids:
        logger.info("No new bids to notify")
        return 0
    
    count = 0
    for bid in bids[:10]:  # Max 10 per run
        dist = f"{bid['distance_miles']:.0f} mi" if bid.get('distance_miles') else "? mi"
        value = f"Est: ${bid['estimated_value']:,.0f}" if bid.get('estimated_value') else ""
        due = f"Due: {bid['due_date'][:10]}" if bid.get('due_date') else ""
        
        desc = (bid.get('description') or '')[:200]
        contact_parts = []
        if bid.get('contact_name'): contact_parts.append(bid['contact_name'])
        if bid.get('contact_email'): contact_parts.append(bid['contact_email'])
        contact = " · ".join(contact_parts)
        
        msg = f"""🏗️ <b>NEW BID</b> — Score: {bid['relevance_score']}

<b>{bid['title']}</b>
{bid.get('agency', '')}
📍 {dist} | {due} | {value}

{desc}

{f'Contact: {contact}' if contact else ''}
🔗 {bid.get('external_url', '')}
Source: {bid['source']}"""
        
        if send_telegram(msg.strip()):
            count += 1
    
    if count:
        mark_notified([b['id'] for b in bids[:10]])
        logger.info(f"Notified {count} new bids")
    
    return count
