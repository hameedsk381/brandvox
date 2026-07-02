export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  agency_id: string | null;
  client_id: string | null;
  location_id: string | null;
  created_at: string;
}

export interface BrandingConfig {
  id: string;
  agency_id: string;
  company_name: string | null;
  logo_url: string | null;
  favicon_url: string | null;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  dark_mode_default: boolean;
  sidebar_style: string;
  login_bg_image: string | null;
  custom_css: string | null;
}

export interface Agency {
  id: string;
  name: string;
  slug: string;
  settings: Record<string, any>;
  created_at: string;
  branding_config?: BrandingConfig;
  razorpay_customer_id?: string | null;
  subscription_plan?: string;
  subscription_status?: string;
  trial_ends_at?: string | null;
}

export interface Client {
  id: string;
  agency_id: string;
  name: string;
  industry: string | null;
  settings: Record<string, any>;
  created_at: string;
}

export interface Location {
  id: string;
  client_id: string;
  name: string;
  address: string | null;
  google_place_id: string | null;
  google_location_id?: string | null;
  last_sync_time?: string | null;
  timezone: string;
  created_at: string;
}

export interface SentimentResult {
  sentiment: "positive" | "negative" | "neutral" | "mixed";
  confidence: number;
  emotions: string[];
}

export interface TopicResult {
  topic: string;
  sub_topic: string | null;
  sentiment: string | null;
}

export interface ReviewReply {
  id: string;
  review_id: string;
  content: string;
  status: "draft" | "approved" | "posted" | "rejected" | "replaced";
  generated_by: "ai" | "manual";
  approved_by: string | null;
  created_at: string;
  approved_by_user?: {
    name: string;
    email: string;
  };
}

export interface Review {
  id: string;
  location_id: string;
  source: string;
  source_review_id: string;
  author_name: string | null;
  author_image_url: string | null;
  rating: number;
  text: string | null;
  review_date: string;
  created_at: string;
  sentiment_result?: SentimentResult;
  topic_results?: TopicResult[];
  replies?: ReviewReply[];
}

export interface BrandVoiceProfile {
  id: string;
  client_id: string;
  tone: string;
  vocabulary_notes: string | null;
  greeting_style: string | null;
  closing_style: string | null;
  example_replies: string[];
  personality_traits: string[];
  created_at: string;
}

export interface SmartRule {
  id: string;
  location_id: string;
  min_rating: number;
  max_rating: number;
  action: "auto_reply" | "approval_required" | "escalate" | "never_auto";
  notify_roles: string[];
  is_active: boolean;
  created_at: string;
}

export interface DashboardData {
  reputation_score: number;
  avg_rating: number;
  total_reviews: number;
  response_rate: number;
  sentiment_score: number;
  review_growth: number;
  rating_trend: { date: string; avg_rating: number; review_count: number }[];
  sentiment_distribution: { positive: number; negative: number; neutral: number; mixed: number };
  recent_reviews: Review[];
  ai_recommendations: { id: string; type: string; title: string; description: string; target_url?: string }[];
  top_topics: { name: string; count: number; sentiment_score: number }[];
}

export interface ForecastHistoricalDataPoint {
  month: string;
  average_rating: number;
  review_volume: number;
}

export interface ForecastResponse {
  id: string;
  location_id: string;
  forecast_date: string;
  predicted_rating: number;
  predicted_volume: number;
  churn_risk_score: number;
  reputation_risks: string[];
  seasonal_trends: string[];
  actionable_advice: string;
  historical_data: ForecastHistoricalDataPoint[];
}
