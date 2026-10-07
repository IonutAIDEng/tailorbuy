# TailorBuy — Improvement Proposals

Ordered by priority and implementation complexity.

---

## 1. eMAG Affiliate API Integration
**Priority:** High  
**Phase:** Post-MVP

eMAG has an affiliate/partner API that exposes real product data: names, prices, stock, ratings, delivery options, images — all in real time.

Why: Gemini Search Grounding is great for discovery, but eMAG API gives exact Romanian market data with live prices and stock availability. Combine both: eMAG API as primary source, Gemini grounding as fallback.

Steps:
- Register for eMAG Affiliate Program
- Get API key
- Build `emag_service.py` that queries products by category/keyword
- Pass results to Gemini for preference-based ranking

---

## 2. pgvector — Semantic Personalization
**Priority:** High  
**Phase:** Post-MVP

Add the `pgvector` extension to PostgreSQL. Store embedding vectors for products the user has interacted with (saved, clicked, rated positively). At search time, retrieve products semantically similar to the user's historical preferences.

Why: This transforms the app from a search tool into a personalized recommendation engine. It also demonstrates a high-value AI Engineering skill — vector similarity search inside the existing PostgreSQL instance, no separate vector DB needed.

Steps:
- Enable `pgvector` extension in PostgreSQL
- Add `embedding` column (vector type) to products table
- Generate embeddings via Gemini Embedding API or sentence-transformers
- Implement cosine similarity query to enrich search results with personal history

---

## 3. Saved Products — Coș de Cumpărături (Basket / Wishlist)
**Priority:** High
**Phase:** Post-MVP

Allow users to bookmark/save any product from the search results so they can review it later. A dedicated screen (e.g. "Salvate" tab) shows all saved products with the option to remove each one.

UI:
- Bookmark icon on each product card in the results screen.
- Tapping it saves the product; tapping again removes it (toggle).
- Saved tab shows the full list sorted by save date descending.
- Each item in the list has a remove button (swipe or trash icon).

Implementation notes:
- New table: `saved_products` (user_id, product snapshot as JSON, saved_at).
- Store a snapshot of the product (name, price, url, store, image_url) at save time — prices change, so we capture what the user saw.
- New endpoints: `POST /saved/{user_id}`, `GET /saved/{user_id}`, `DELETE /saved/{user_id}/{product_id}`.
- The saved list does NOT re-query Gemini — it shows the exact snapshot saved.

---

## 4. User Feedback Loop
**Priority:** Medium  
**Phase:** Post-MVP

Capture explicit and implicit user signals to improve future recommendations.

Feedback signal hierarchy (strongest → weakest):
1. User explicitly rates a product (1–5 stars) — strongest signal
2. User marks "not relevant" — strong negative
3. User saves/bookmarks a product — strong positive
4. User opens product detail — weak positive
5. User ignores result — ambiguous, do NOT treat as negative

Important: unchosen results from a search are NOT negative signals (user may have liked several but only needed one). Only treat explicit dismissals as negatives.

Store in: `user_product_interactions` table with action type and timestamp.

---

## 4. Multi-Store Support (Altex, Media Galaxy, Cel.ro)
**Priority:** Medium  
**Phase:** Scaling

Extend search beyond eMAG. Check if Altex/Media Galaxy have affiliate APIs. If not, evaluate legal scraping options or use Gemini Search Grounding to surface their products.

Enables: price comparison across stores — a key differentiator.

---

## 5. Price Tracking & Alerts
**Priority:** Low  
**Phase:** Scaling

Allow users to track a product and receive a notification when the price drops below a threshold. Requires a background job (e.g., Celery + Redis) that periodically checks prices.

---

## 6. Preferred Store Selection (User-Configurable)
**Priority:** Medium  
**Phase:** Post-MVP

Allow users to select which e-commerce sites they prefer via a checklist in the Profile screen (eMAG, Altex, Cel.ro, Flanco, PCGarage, Evomag, etc.). Add a toggle: "Search only on selected sites".

Behaviour:
- Toggle OFF (default): AI searches selected sites first and prioritises their results, but also searches other Romanian stores to check for better results.
- Toggle ON: AI is explicitly instructed to search ONLY on the selected sites and must not return products from any other source.

Implementation notes:
- Store selected sites + toggle as part of `UserPreference` (new columns or JSON column).
- Prompt builder reads the site list and injects either `site:emag.ro OR site:altex.ro` (toggle ON) or a prioritised search with a broad fallback (toggle OFF).
- Profile screen: scrollable checklist of supported stores, each with logo/name, plus the "Search only here" toggle.

---

## 7. SerpAPI as Search Fallback
**Priority:** Low  
**Phase:** Scaling

SerpAPI provides high-quality structured Google Shopping results. Use as a fallback when Gemini Search Grounding quota is exceeded or for categories where grounding underperforms.

Cost consideration: ~$50/month for 5000 searches. Evaluate at scale.
