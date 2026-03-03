#!/bin/bash
cd /root/clawd/brad-v2

# Run scrapers
/usr/bin/python3 run.py

# Deploy dashboard to Cloudflare Pages
export CLOUDFLARE_API_TOKEN="0l-OFc_P00fZZG8S13BMQYSELGn5-yQxJRRfaR8Y"
export CLOUDFLARE_ACCOUNT_ID="e1610a51bf2727c3ccbac32d08639d47"
wrangler pages deploy dashboard/ --project-name brad-v2

echo "$(date): Deploy complete" >> /root/clawd/brad-v2/cron.log
