export interface TokenData {
  access_token: string;
  token_type?: string;
}

export interface TrackedItem {
  id: number;
  name: string;
  keywords: string;
  sku: string | null;
  mpn: string | null;
  category_id: string | null;
  marketplace: string;
  target_price: number | null;
  alert_threshold: number;
  min_deal_score: number;
  is_enabled: boolean;
  search_interval: number;
  scam_floor: number | null;
  benchmark_median: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  last_searched: string | null;
  priority_tier: string;
}

export interface TrackedItemStats {
  total_items: number;
  enabled_items: number;
  p0_count: number;
  p1_count: number;
  p2_count: number;
  p3_count: number;
  estimated_daily_calls: number;
}

export interface ItemsListResponse {
  items: TrackedItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface ToggleResponse {
  id: number;
  is_enabled: boolean;
}

export interface BulkUpdateResponse {
  updated: number;
  action: string;
}

export interface DealScore {
  overall_score: number;
  deal_score: number;
  confidence: number;
  classification: string;
  price_zscore: number | null;
  vs_median_pct: number | null;
  est_fair_value: number | null;
  scam_warning: string | null;
}

/**
 * Per-listing origin source (feature-003). The /deals payload spreads the
 * Listing columns including `source`; the frontend renders it as a SOURCE badge.
 * Common values: 'ebay' | 'shopify' | 'pcpartpicker'. Unknown values degrade
 * gracefully to a neutral chip.
 */
export type ListingSource = "ebay" | "shopify" | "pcpartpicker" | (string & {});

export interface Deal {
  id: number;
  marketplace_id: string;
  tracked_item_id: number | null;
  title: string;
  price: number;
  shipping: number;
  seller: string;
  seller_feedback: number;
  seller_positive_pct: number;
  condition: string | null;
  url: string;
  image_url: string | null;
  is_auction: boolean;
  quantity: number;
  listing_date: string;
  end_date: string | null;
  /** Origin source for the SOURCE badge (additive, feature-005). */
  source?: ListingSource | null;
  score?: DealScore;
}

export interface DealsListResponse {
  deals: Deal[];
  total: number;
  page: number;
  per_page: number;
}

export interface BudgetStatus {
  calls_today: number;
  daily_limit: number;
  remaining: number;
  buffer: number;
  utilization_pct: number;
  status: "ok" | "warning" | "critical";
  searches_possible: number;
}

export interface Preset {
  interval: number;
  label: string;
  daily_calls: number;
}

export interface PresetsResponse {
  presets: Record<string, Preset>;
}

export interface Alert {
  id: number;
  listing_id: number;
  tracked_item_id: number;
  score_id: number | null;
  channel: string;
  alert_type: string;
  was_sent: boolean;
  sent_at: string | null;
  template_used: string | null;
  telegram_msg_id: string | null;
  error_message: string | null;
  created_at: string;
}

export interface AlertsListResponse {
  alerts: Alert[];
  total: number;
  page: number;
  per_page: number;
}

export interface NotificationSettings {
  id: number;
  user_id: number;
  telegram_chat_id: string | null;
  telegram_enabled: boolean;
  email_address: string | null;
  email_enabled: boolean;
  email_digest_mode: string;
  telegram_min_score: number;
  email_min_score: number;
  ntfy_enabled: boolean;
  ntfy_topic: string | null;
  ntfy_min_score: number;
  mute_until: string | null;
}

export interface CatalogSuggestion {
  name: string;
  keywords: string;
  sku: string;
  mpn: string;
  category_id: string;
  target_price: number;
  alert_threshold: number;
  search_interval: number;
  benchmark_median: number;
  scam_floor: number;
  notes: string;
}

export interface Category {
  id: string;
  name: string;
}

/**
 * AI analysis for a single listing (feature-006). GET /api/v1/ai/{listing_id}
 * returns { analysis: null } when no analysis exists — also the de-facto
 * AI-disabled signal (there is no JSON feature-flag endpoint).
 */
export interface AiAnalysis {
  deal_grade: string | null;
  reasoning: string | null;
  scam_signal: boolean;
  scam_reasons: string[] | null;
  extracted_specs: Record<string, unknown> | null;
  provider: string;
  model: string;
  created_at: string | null;
}

export interface AiAnalysisResponse {
  analysis: AiAnalysis | null;
}

export interface SearchTriggerResponse {
  listings_found: number;
  new_listings: number;
  duplicates_skipped: number;
  duration_ms: number;
}

export interface SearchTriggerAllResponse {
  items_processed: number;
  total_listings: number;
  total_new: number;
  total_duplicates: number;
}
