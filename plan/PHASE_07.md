# PHASE 07 — n8n Workflow Definitions

## Objective
Create 4 production-ready n8n workflow JSON files that orchestrate the deal tracking pipeline: marketplace polling, deal scoring, notification routing, and daily analytics.

---

## Output Location
`/mnt/agents/output/hardware-deal-tracker/project/workflows/`

---

## Dependencies
- Phase 2 (API endpoints) merged to `main`
- Phase 3 (eBay ingestion) merged
- Phase 4 (deal scoring) merged
- Phase 5 (notifications) merged
- Branch from: `main`

---

## n8n Configuration

**Connection setup for self-hosted n8n:**
- Base URL: `http://n8n:5678`
- Backend API base: `http://backend:8000/api/v1`
- PostgreSQL connection to same DB as backend
- Webhook triggers for inter-workflow communication

---

## Tasks

### Task 1: Workflow 1 — Marketplace Poller (`workflows/marketplace-poller.json`)

**Trigger:** Cron (every 5 minutes: `0 */5 * * * *`)

**Workflow logic:**
1. **Schedule Trigger** — Cron node
2. **Get Items to Poll** — PostgreSQL node:
   ```sql
   SELECT id, name, keywords, category_id, last_searched, search_interval
   FROM tracked_items
   WHERE is_enabled = true
     AND (last_searched IS NULL 
          OR last_searched < NOW() - (search_interval || ' seconds')::INTERVAL)
   ORDER BY last_searched NULLS FIRST
   LIMIT 5
   ```
3. **Split Items** — Split In Batches node (1 item per batch)
4. **Trigger Search** — HTTP Request node:
   ```
   POST http://backend:8000/api/v1/search/trigger/{{ $json.id }}
   Headers: { "Authorization": "Bearer {{ $credentials.backend_token }}" }
   ```
5. **Log Result** — PostgreSQL node:
   ```sql
   INSERT INTO search_logs (tracked_item_id, listings_found, new_listings, 
                           duplicates_skipped, duration_ms, created_at)
   VALUES ({{ $json.id }}, {{ $json.listings_found }}, {{ $json.new_listings }},
           {{ $json.duplicates_skipped }}, {{ $json.duration_ms }}, NOW())
   ```
6. **If New Listings > 0** — IF node
7. **Trigger Deal Scoring** — HTTP Request node (webhook to Workflow 2):
   ```
   POST http://n8n:5678/webhook/deal-scorer
   Body: { "tracked_item_id": {{ $json.id }} }
   ```

### Task 2: Workflow 2 — Deal Scorer (`workflows/deal-scorer.json`)

**Trigger:** Webhook (`POST /webhook/deal-scorer`)

**Workflow logic:**
1. **Webhook Trigger** — Webhook node (POST)
2. **Get Unscored Listings** — PostgreSQL node:
   ```sql
   SELECT l.id, l.tracked_item_id, l.price, l.shipping, l.title, 
          l.seller, l.seller_feedback, l.seller_positive_pct,
          l.condition, l.quantity
   FROM listings l
   LEFT JOIN listing_scores ls ON l.id = ls.listing_id
   WHERE ls.id IS NULL
     AND l.tracked_item_id = {{ $json.tracked_item_id }}
   ORDER BY l.created_at DESC
   LIMIT 10
   ```
3. **Split Listings** — Split In Batches node
4. **Score Listing** — HTTP Request node:
   ```
   POST http://backend:8000/api/v1/deals/score/{{ $json.id }}
   Headers: { "Authorization": "Bearer {{ $credentials.backend_token }}" }
   ```
5. **If Score >= 50** — IF node
6. **Trigger Notifications** — HTTP Request node (webhook to Workflow 3):
   ```
   POST http://n8n:5678/webhook/notification-router
   Body: { "listing_id": {{ $json.id }}, "score_id": {{ $json.score_id }} }
   ```

### Task 3: Workflow 3 — Notification Router (`workflows/notification-router.json`)

**Trigger:** Webhook (`POST /webhook/notification-router`)

**Workflow logic:**
1. **Webhook Trigger** — Webhook node
2. **Get Listing + Score** — PostgreSQL node:
   ```sql
   SELECT l.id, l.title, l.price, l.shipping, l.seller, 
          l.seller_feedback, l.seller_positive_pct, l.url, l.image_url,
          l.tracked_item_id, ls.overall_score, ls.classification,
          ls.vs_median_pct, ls.est_fair_value
   FROM listings l
   JOIN listing_scores ls ON l.id = ls.listing_id
   WHERE l.id = {{ $json.listing_id }}
     AND ls.id = {{ $json.score_id }}
   ```
3. **Get User Settings** — PostgreSQL node:
   ```sql
   SELECT * FROM notification_settings WHERE user_id = 1 LIMIT 1
   ```
4. **Route Telegram** — IF node (telegram_enabled AND score >= telegram_min_score):
   - **Send Telegram** — Telegram node:
     ```
     Chat ID: {{ $json.telegram_chat_id }}
     Text: 🔥 *DEAL ALERT* — Score: {{ $json.overall_score }}/100
     
     📦 {{ $json.title }}
     💰 ${{ $json.price }} (Est. value: ${{ $json.est_fair_value }})
     {{ $json.vs_median_pct > 0 ? '📉 ' + ($json.vs_median_pct * 100) + '% below median' : '' }}
     🔗 {{ $json.url }}
     ```
5. **Route Email** — IF node (email_enabled AND score >= email_min_score AND email_digest_mode == "instant"):
   - **Send Email** — Email (SMTP) node:
     ```
     To: {{ $json.email_address }}
     Subject: Deal Alert: {{ $json.title[:50] }} — Score {{ $json.overall_score }}
     Body: HTML template
     ```
6. **Record Alert** — PostgreSQL node:
   ```sql
   INSERT INTO alerts (listing_id, tracked_item_id, score_id, channel, 
                       alert_type, was_sent, sent_at, created_at)
   VALUES ({{ $json.listing_id }}, {{ $json.tracked_item_id }}, {{ $json.score_id }},
           '{{ $json.channel }}', 'instant', true, NOW(), NOW())
   ```

### Task 4: Workflow 4 — Daily Analytics (`workflows/daily-analytics.json`)

**Trigger:** Cron (daily at 8:00 AM: `0 8 * * *`)

**Workflow logic:**
1. **Schedule Trigger** — Cron node
2. **Generate Summary** — HTTP Request node:
   ```
   GET http://backend:8000/api/v1/stats/daily
   Headers: { "Authorization": "Bearer {{ $credentials.backend_token }}" }
   ```
3. **Build Email** — Code node (JavaScript):
   ```javascript
   const stats = $input.first().json;
   const html = `
     <h2>📊 Hardware Deal Tracker — Daily Summary</h2>
     <p>${stats.date}</p>
     <ul>
       <li>New listings: ${stats.new_listings}</li>
       <li>Deals scored: ${stats.deals_scored}</li>
       <li>Average deal score: ${stats.avg_score}</li>
       <li>Hot deals (85+): ${stats.hot_deals}</li>
       <li>Alerts sent: ${stats.alerts_sent}</li>
     </ul>
     ${stats.top_deals.map(d => `<p><strong>${d.title}</strong> — Score: ${d.score} — $${d.price}</p>`).join('')}
   `;
   return [{ json: { html, subject: `Daily Deal Digest — ${stats.date}` } }];
   ```
4. **Get Subscribers** — PostgreSQL node:
   ```sql
   SELECT email_address FROM notification_settings 
   WHERE email_enabled = true AND email_digest_mode = 'daily'
   ```
5. **Send Digest** — Split In Batches + Email (SMTP) node
6. **Record Analytics** — PostgreSQL node:
   ```sql
   INSERT INTO daily_analytics (date, new_listings, deals_scored, avg_score, 
                                hot_deals, alerts_sent, created_at)
   VALUES (CURRENT_DATE, {{ $json.new_listings }}, {{ $json.deals_scored }},
           {{ $json.avg_score }}, {{ $json.hot_deals }}, {{ $json.alerts_sent }}, NOW())
   ```

---

## Deliverables

- [ ] `workflows/marketplace-poller.json` — eBay polling workflow
- [ ] `workflows/deal-scorer.json` — Deal scoring trigger workflow
- [ ] `workflows/notification-router.json` — Alert dispatch workflow
- [ ] `workflows/daily-analytics.json` — Daily digest workflow
- [ ] `scripts/import-workflows.sh` — Script to import workflows via n8n API
- [ ] `workflows/README.md` — Setup instructions for each workflow

## Workflow Import Script

```bash
#!/bin/bash
# scripts/import-workflows.sh
N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_USER="${N8N_BASIC_AUTH_USER:-admin}"
N8N_PASS="${N8N_BASIC_AUTH_PASSWORD:-admin}"

for workflow in workflows/*.json; do
  echo "Importing $(basename $workflow)..."
  curl -s -X POST "$N8N_URL/api/v1/workflows" \
    -u "$N8N_USER:$N8N_PASS" \
    -H "Content-Type: application/json" \
    -d @$workflow
done
echo "Done! Activate workflows in the n8n UI."
```

## Git
Branch: `phase-07-n8n`
Base: `main` (after Phases 2-5 merged)
Commit message: `feat(phase-7): n8n workflow definitions for polling, scoring, notifications, analytics`
