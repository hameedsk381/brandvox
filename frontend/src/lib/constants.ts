export const ROUTES = {
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  REVIEWS: "/dashboard/reviews",
  ANALYTICS: "/dashboard/analytics",
  REPORTS: "/dashboard/reports",
  INTEGRATIONS: "/dashboard/integrations",
  COPILOT: "/dashboard/copilot",
  COMPETITORS: "/dashboard/competitors",
  ALERTS: "/dashboard/alerts",
  FORECASTING: "/dashboard/analytics/forecasting",
  SETTINGS: "/dashboard/settings",
  BRANDING: "/dashboard/settings/branding",
  BRAND_VOICE: "/dashboard/settings/brand-voice",
  SMART_RULES: "/dashboard/settings/smart-rules",
  TEAM: "/dashboard/settings/team",
  AUDIT_LOGS: "/dashboard/settings/audit-logs",
  SECURITY: "/dashboard/settings/security",
  REVIEW_CAMPAIGNS: "/dashboard/review-campaigns",
  SEO: "/dashboard/seo",
  FORGOT_PASSWORD: "/forgot-password",
  RESET_PASSWORD: "/reset-password",
};

export const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  agency_admin: "Agency Admin",
  client_admin: "Client Admin",
  marketing_manager: "Marketing Manager",
  customer_support: "Customer Support",
  branch_manager: "Branch Manager",
  read_only: "Read Only",
};

export const SENTIMENT_COLORS: Record<string, string> = {
  positive: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  negative: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  neutral: "text-muted-foreground bg-zinc-500/10 border-zinc-500/20",
  mixed: "text-amber-400 bg-amber-500/10 border-amber-500/20",
};

export const RATING_COLORS: Record<number, string> = {
  5: "text-emerald-400",
  4: "text-teal-400",
  3: "text-amber-400",
  2: "text-orange-400",
  1: "text-rose-400",
};
