import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("heron_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirect to login on 401 (except on auth pages themselves)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (
      err.response?.status === 401 &&
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/auth") &&
      !window.location.pathname.startsWith("/scan")
    ) {
      localStorage.removeItem("heron_token");
      window.location.href = "/auth/login";
    }
    return Promise.reject(err);
  }
);

export const heronApi = {
  // Domain scans
  freemiumScan: (domain: string, annualRevenue: number, email: string) =>
    api.post("/freemium/scan", { domain, annual_revenue_eur: annualRevenue, email }),

  startScan: (domain: string, annualRevenue: number, planTier: string) =>
    api.post("/scan", { domain, annual_revenue_eur: annualRevenue, plan_tier: planTier }),

  listScans: (page = 1) => api.get("/scan", { params: { page } }),

  getScanStatus: (scanId: string) => api.get(`/scan/${scanId}`),

  getScanClaims: (scanId: string) => api.get(`/scan/${scanId}/claims`),

  getReport: (scanId: string) => api.get(`/report/${scanId}`),

  downloadPdf: (scanId: string) => api.get(`/report/${scanId}/pdf`, { responseType: "blob" }),

  // Billing
  createCheckout: (plan: string, scanId?: string) =>
    api.post("/billing/checkout", { plan, scan_id: scanId }),

  // Auth
  login: (email: string, password: string) => api.post("/auth/login", { email, password }),

  register: (email: string, password: string) => api.post("/auth/register", { email, password }),

  // Legal corpus
  getCorporaIndex: () => api.get("/corpus"),

  getCorpus: (corpusId: string) => api.get(`/corpus/${corpusId}`),

  getArticle: (corpusId: string, articleId: string) =>
    api.get(`/corpus/${corpusId}/articles/${articleId}`),

  // Evidence
  getCertificationTypes: () => api.get("/evidence/certification-types"),

  getUserEvidence: () => api.get("/evidence"),

  getEvidenceSummary: () => api.get("/evidence/summary"),

  uploadEvidence: (formData: FormData) =>
    api.post("/evidence", formData, { headers: { "Content-Type": "multipart/form-data" } }),

  deleteEvidence: (evidenceId: string) => api.delete(`/evidence/${evidenceId}`),

  // Ads scans
  startAdsFreemiumScan: (
    inputType: string,
    inputTitle: string,
    text: string,
    annualRevenue: number,
    email: string
  ) =>
    api.post("/ads/scan", {
      input_type: inputType,
      input_title: inputTitle || null,
      input_text: text,
      annual_revenue_eur: annualRevenue,
      email,
    }),

  startAdsPaidScan: (inputType: string, inputTitle: string, text: string, annualRevenue: number) =>
    api.post("/ads/scan", {
      input_type: inputType,
      input_title: inputTitle || null,
      input_text: text,
      annual_revenue_eur: annualRevenue,
    }),

  getAdsScan: (scanId: string, email?: string) =>
    api.get(`/ads/scan/${scanId}`, { params: email ? { email } : undefined }),

  downloadAdsPdf: (scanId: string) =>
    api.get(`/ads/scan/${scanId}/pdf`, { responseType: "blob" }),

  // Admin
  getAdminStats: () => api.get("/admin/stats"),

  getAdminScans: (scanType: "domain" | "ads", status?: string, page = 1) =>
    api.get("/admin/scans", { params: { scan_type: scanType, status, page } }),

  getAdminEvidence: (verified?: number) =>
    api.get("/admin/evidence", { params: verified !== undefined ? { verified } : undefined }),

  verifyEvidence: (evidenceId: string, verified: 0 | 1 | 2) =>
    api.post(`/admin/evidence/${evidenceId}/verify`, { verified }),

  reloadCorpus: () => api.post("/admin/corpus/reload"),

  triggerExpiryCheck: () => api.post("/admin/evidence/expiry-check"),
};

export default api;
