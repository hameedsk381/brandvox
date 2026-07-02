import axios, { AxiosError } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

export function getErrorMessage(error: unknown, fallback = "An unexpected error occurred"): string {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as ApiErrorResponse;
    if (data.detail) return data.detail;
    if (data.message) return data.message;
    if (data.errors) {
      return Object.values(data.errors).flat().join(", ");
    }
  }
  if (error instanceof Error) return error.message;
  return fallback;
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to automatically add authorization token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const authData = localStorage.getItem("auth-storage");
      if (authData) {
        try {
          const parsed = JSON.parse(authData);
          const token = parsed.state?.token;
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch (e) {
          console.error("Error parsing auth storage token:", e);
        }
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiration/401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      import("react-hot-toast").then(({ default: toast }) => {
        toast.error("Session expired. Please sign in again.");
      });
      localStorage.removeItem("auth-storage");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = `/login?msg=session_expired`;
      }
    }
    return Promise.reject(error);
  }
);

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface CreateClientData {
  name: string;
  industry?: string;
  settings?: Record<string, unknown>;
}

export interface CreateLocationData {
  client_id: string;
  name: string;
  address?: string;
  google_place_id?: string;
  timezone?: string;
}

export interface ReviewsListParams {
  location_id?: string;
  rating?: number;
  sentiment?: string;
  source?: string;
  search?: string;
  reply_status?: string;
  page?: number;
  per_page?: number;
}

export interface CreateReviewData {
  location_id: string;
  source: string;
  source_review_id?: string;
  author_name?: string;
  rating: number;
  text?: string;
  review_date?: string;
}

export interface SubmitReplyData {
  content: string;
}

export interface UpdateBrandingData {
  company_name?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  font_family?: string;
  dark_mode_default?: boolean;
  sidebar_style?: string;
  logo_url?: string;
  favicon_url?: string;
}

export interface UpdateBrandVoiceData {
  tone?: string;
  vocabulary_notes?: string | null;
  greeting_style?: string | null;
  closing_style?: string | null;
  example_replies?: string[];
  personality_traits?: string[];
}

export interface UpdateSmartRulesData {
  min_rating?: number;
  max_rating?: number;
  action?: "auto_reply" | "approval_required" | "escalate" | "never_auto";
  notify_roles?: string[];
  is_active?: boolean;
}

export interface CreateUserData {
  email: string;
  name: string;
  role: string;
  password?: string;
  client_id?: string;
  location_id?: string;
}

export type ReportFormat = "pdf" | "csv" | "xlsx" | "pptx";
export type ReportType = "summary" | "detailed" | "sentiment" | "comparison";

// ---------------- API SERVICES ----------------

export const authAPI = {
  login: async (data: LoginData) => {
    const res = await api.post("/api/auth/login", data);
    return res.data;
  },
  register: async (data: RegisterData) => {
    const res = await api.post("/api/auth/register", data);
    return res.data;
  },
  getMe: async () => {
    const res = await api.get("/api/auth/me");
    return res.data;
  },
  changePassword: async (data: { current_password: string; new_password: string }) => {
    const res = await api.patch("/api/auth/password", data);
    return res.data;
  },
  forgotPassword: async (data: { email: string }) => {
    const res = await api.post("/api/auth/forgot-password", data);
    return res.data;
  },
  resetPassword: async (data: { token: string; password: string }) => {
    const res = await api.post("/api/auth/reset-password", data);
    return res.data;
  },
  setupMfa: async () => {
    const res = await api.post("/api/auth/mfa/setup");
    return res.data;
  },
  verifyMfa: async (data: { code: string }) => {
    const res = await api.post("/api/auth/mfa/verify", data);
    return res.data;
  },
  disableMfa: async (data: { code: string }) => {
    const res = await api.post("/api/auth/mfa/disable", data);
    return res.data;
  },
  verifyMfaLogin: async (data: { mfa_token: string; code: string }) => {
    const res = await api.post("/api/auth/mfa/verify-login", data);
    return res.data;
  },
  mfaStatus: async () => {
    const res = await api.get("/api/auth/mfa/status");
    return res.data;
  },
};
export const userAPI = {
  exportMyData: async () => {
    const res = await api.get("/api/users/me/export");
    return res.data;
  },
  deleteMyAccount: async () => {
    const res = await api.delete("/api/users/me");
    return res.data;
  },
};

export const tenantAPI = {
  getClients: async () => {
    const res = await api.get("/api/clients");
    return res.data;
  },
  createClient: async (data: CreateClientData) => {
    const res = await api.post("/api/clients", data);
    return res.data;
  },
  getLocations: async () => {
    const res = await api.get("/api/locations");
    return res.data;
  },
  createLocation: async (data: CreateLocationData) => {
    const res = await api.post("/api/locations", data);
    return res.data;
  },
};

export const reviewsAPI = {
  list: async (params?: ReviewsListParams) => {
    const res = await api.get("/api/reviews", { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get(`/api/reviews/${id}`);
    return res.data;
  },
  create: async (data: CreateReviewData) => {
    const res = await api.post("/api/reviews", data);
    return res.data;
  },
  generateAIReply: async (id: string) => {
    const res = await api.post(`/api/reviews/${id}/generate-reply`);
    return res.data;
  },
  submitReply: async (id: string, data: SubmitReplyData) => {
    const res = await api.post(`/api/reviews/${id}/reply`, data);
    return res.data;
  },
  approveReply: async (replyId: string) => {
    const res = await api.patch(`/api/replies/${replyId}/approve`);
    return res.data;
  },
  rejectReply: async (replyId: string) => {
    const res = await api.patch(`/api/replies/${replyId}/reject`);
    return res.data;
  },
};

export const analyticsAPI = {
  getDashboard: async () => {
    const res = await api.get("/api/dashboard");
    return res.data;
  },
  getSentiment: async () => {
    const res = await api.get("/api/analytics/sentiment");
    return res.data;
  },
};

export const settingsAPI = {
  getBranding: async (agencyId: string) => {
    const res = await api.get(`/api/branding/${agencyId}`);
    return res.data;
  },
  updateBranding: async (agencyId: string, data: UpdateBrandingData) => {
    const res = await api.put(`/api/branding/${agencyId}`, data);
    return res.data;
  },
  getBrandVoice: async (clientId: string) => {
    const res = await api.get(`/api/brand-voice/${clientId}`);
    return res.data;
  },
  updateBrandVoice: async (clientId: string, data: UpdateBrandVoiceData) => {
    const res = await api.put(`/api/brand-voice/${clientId}`, data);
    return res.data;
  },
  getSmartRules: async (locationId: string) => {
    const res = await api.get(`/api/smart-rules/${locationId}`);
    return res.data;
  },
  updateSmartRules: async (locationId: string, data: UpdateSmartRulesData | UpdateSmartRulesData[]) => {
    const res = await api.put(`/api/smart-rules/${locationId}`, data);
    return res.data;
  },
  getUsers: async () => {
    const res = await api.get("/api/users");
    return res.data;
  },
  createUser: async (data: CreateUserData) => {
    const res = await api.post("/api/users", data);
    return res.data;
  },
};

export const reportsAPI = {
  download: async (format: ReportFormat, type: ReportType) => {
    const res = await api.post(
      `/api/reports/generate?format=${format}&report_type=${type}`,
      {},
      { responseType: "blob" }
    );
    return res.data;
  },
};

export const competitorsAPI = {
  list: async (locationId: string) => {
    const res = await api.get(`/api/competitors?location_id=${locationId}`);
    return res.data;
  },
  create: async (locationId: string, name: string, googlePlaceId?: string) => {
    const res = await api.post(`/api/competitors?location_id=${locationId}`, { name, google_place_id: googlePlaceId || null });
    return res.data;
  },
  delete: async (locationId: string, competitorId: string) => {
    const res = await api.delete(`/api/competitors/${competitorId}?location_id=${locationId}`);
    return res.data;
  },
  getAnalytics: async (locationId: string) => {
    const res = await api.get(`/api/competitors/analytics?location_id=${locationId}`);
    return res.data;
  },
  getAnalysis: async (locationId: string) => {
    const res = await api.get(`/api/competitors/analysis?location_id=${locationId}`);
    return res.data;
  },
  triggerAnalysis: async (locationId: string) => {
    const res = await api.post(`/api/competitors/analyze?location_id=${locationId}`);
    return res.data;
  },
};

export const alertsAPI = {
  list: async (locationId: string) => {
    const res = await api.get(`/api/alerts?location_id=${locationId}`);
    return res.data;
  },
  resolve: async (locationId: string, alertId: string) => {
    const res = await api.patch(`/api/alerts/${alertId}/resolve?location_id=${locationId}`);
    return res.data;
  },
  getIntegrations: async (locationId: string) => {
    const res = await api.get(`/api/alerts/integrations?location_id=${locationId}`);
    return res.data;
  },
  upsertIntegration: async (locationId: string, type: string, webhookUrl: string, isActive: boolean) => {
    const res = await api.post(`/api/alerts/integrations?location_id=${locationId}`, {
      type,
      webhook_url: webhookUrl,
      is_active: isActive
    });
    return res.data;
  }
};

export const forecastingAPI = {
  get: async (locationId: string) => {
    const res = await api.get(`/api/forecasting?location_id=${locationId}`);
    return res.data;
  }
};

export const googleIntegrationsAPI = {
  getStatus: async (clientId: string, locationId?: string) => {
    const res = await api.get("/api/integrations/google/status", {
      params: {
        client_id: clientId,
        location_id: locationId,
      },
    });
    return res.data;
  },
  getAuthUrl: async (clientId: string) => {
    const res = await api.get(`/api/integrations/google/auth-url?client_id=${clientId}`);
    return res.data;
  },
  getLocations: async (clientId: string) => {
    const res = await api.get(`/api/integrations/google/locations?client_id=${clientId}`);
    return res.data;
  },
  mapLocation: async (locationId: string, googleLocationId: string) => {
    const res = await api.post(
      `/api/integrations/google/map-location?location_id=${locationId}&google_location_id=${encodeURIComponent(googleLocationId)}`
    );
    return res.data;
  },
  syncLocation: async (locationId: string) => {
    const res = await api.post(`/api/integrations/google/sync?location_id=${locationId}`);
    return res.data;
  },
};

export const billingAPI = {
  getStatus: async () => {
    const res = await api.get("/api/billing/status");
    return res.data;
  },
  checkout: async (planId: string) => {
    const res = await api.post("/api/billing/checkout", { plan_id: planId });
    return res.data;
  },
};

export const auditAPI = {
  list: async (params?: { action?: string; user_id?: string; resource_type?: string; limit?: number; offset?: number }) => {
    const res = await api.get("/api/audit", { params });
    return res.data;
  }
};

export interface ScheduledReportData {
  name: string;
  report_type?: string;
  format?: string;
  cron_expression?: string;
  recipients?: string[];
  is_active?: boolean;
  client_id?: string;
  location_id?: string;
}

export interface ScheduledReportItem {
  id: string;
  agency_id: string;
  client_id: string | null;
  location_id: string | null;
  name: string;
  report_type: string;
  format: string;
  cron_expression: string;
  recipients: string[];
  is_active: boolean;
  last_sent_at: string | null;
  next_run_at: string | null;
  created_at: string;
}

export const scheduledReportsAPI = {
  list: async () => {
    const res = await api.get("/api/reports/scheduled");
    return res.data as ScheduledReportItem[];
  },
  create: async (data: ScheduledReportData) => {
    const res = await api.post("/api/reports/scheduled", data);
    return res.data as ScheduledReportItem;
  },
  update: async (id: string, data: Partial<ScheduledReportData>) => {
    const res = await api.patch(`/api/reports/scheduled/${id}`, data);
    return res.data as ScheduledReportItem;
  },
  delete: async (id: string) => {
    await api.delete(`/api/reports/scheduled/${id}`);
  }
};
