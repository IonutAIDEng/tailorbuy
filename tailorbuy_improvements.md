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

## 3. User Feedback Loop
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

## 6. SerpAPI as Search Fallback
**Priority:** Low  
**Phase:** Scaling

SerpAPI provides high-quality structured Google Shopping results. Use as a fallback when Gemini Search Grounding quota is exceeded or for categories where grounding underperforms.

Cost consideration: ~$50/month for 5000 searches. Evaluate at scale.
