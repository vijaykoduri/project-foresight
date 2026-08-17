import axios from 'axios';

const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  return import.meta.env.PROD 
    ? 'https://foresight-backend-808q.onrender.com' 
    : 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.includes('/login')) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const authApi = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
  changePassword: (data) => api.post('/auth/change-password', data),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
};

// Products
export const productsApi = {
  list: (params) => api.get('/products', { params }),
  get: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
  categories: () => api.get('/products/categories'),
};

// Inventory
export const inventoryApi = {
  summary: (params) => api.get('/inventory', { params }),
  get: (productId) => api.get(`/inventory/${productId}`),
  adjust: (data) => api.post('/inventory/adjust', data),
  transactions: (params) => api.get('/inventory/transactions/list', { params }),
};

// Sales
export const salesApi = {
  list: (params) => api.get('/sales', { params }),
  get: (id) => api.get(`/sales/${id}`),
  create: (data) => api.post('/sales', data),
};

// Suppliers
export const suppliersApi = {
  list: (params) => api.get('/suppliers', { params }),
  get: (id) => api.get(`/suppliers/${id}`),
  create: (data) => api.post('/suppliers', data),
  update: (id, data) => api.put(`/suppliers/${id}`, data),
  delete: (id) => api.delete(`/suppliers/${id}`),
};

// Forecast
export const forecastApi = {
  generate: (data) => api.post('/forecast/generate', data),
  get: (productId) => api.get(`/forecast/${productId}`),
};

// Recommendations
export const recommendationsApi = {
  list: (params) => api.get('/recommendations', { params }),
  generate: () => api.post('/recommendations/generate'),
  update: (id, data) => api.put(`/recommendations/${id}`, data),
};

// Alerts
export const alertsApi = {
  list: (params) => api.get('/alerts', { params }),
  generate: () => api.post('/alerts/generate'),
  markRead: (id) => api.put(`/alerts/${id}/read`),
  resolve: (id) => api.put(`/alerts/${id}/resolve`),
};

// Dashboard
export const dashboardApi = {
  summary: () => api.get('/dashboard/summary'),
  revenue: (params) => api.get('/dashboard/revenue', { params }),
  sales: (params) => api.get('/dashboard/sales', { params }),
  inventory: () => api.get('/dashboard/inventory'),
  categoryPerformance: () => api.get('/dashboard/category-performance'),
  topProducts: (params) => api.get('/dashboard/top-products', { params }),
  recentAlerts: () => api.get('/dashboard/recent-alerts'),
  reorderItems: () => api.get('/dashboard/reorder-items'),
  recentTransactions: () => api.get('/dashboard/recent-transactions'),
};

// Analytics
export const analyticsApi = {
  summary: (params) => api.get('/analytics/summary', { params }),
  trends: (params) => api.get('/analytics/trends', { params }),
};

// Reports
export const reportsApi = {
  inventory: () => api.get('/reports/inventory', { responseType: 'blob' }),
  sales: (params) => api.get('/reports/sales', { params, responseType: 'blob' }),
  forecast: () => api.get('/reports/forecast', { responseType: 'blob' }),
  reorder: () => api.get('/reports/reorder', { responseType: 'blob' }),
};

// Users
export const usersApi = {
  list: () => api.get('/users'),
  roles: () => api.get('/users/roles'),
  update: (id, data) => api.put(`/users/${id}`, data),
};

// Health
export const healthApi = {
  check: () => api.get('/health'),
};

export const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
};
