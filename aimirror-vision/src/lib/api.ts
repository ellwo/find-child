import axios from 'axios';

const API_BASE_URL = "";
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (unauthorized)
let isRedirecting = false;
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      // Only redirect if we're not already on the home page and not already redirecting
      const currentPath = window.location.pathname;
      if (currentPath !== '/' && !isRedirecting) {
        isRedirecting = true;
        // Use setTimeout to prevent multiple redirects
        setTimeout(() => {
          window.location.href = '/';
          isRedirecting = false;
        }, 100);
      }
    }
    return Promise.reject(error);
  }
);

// Authentication APIs
export const login = async (username: string, password: string) => {
  // OAuth2PasswordRequestForm expects form data, not JSON
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  const response = await api.post('/api/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const getCurrentUser = async (token?: string) => {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await api.get('/api/auth/me', { headers });
  return response.data;
};

export const refreshToken = async () => {
  const response = await api.post('/api/auth/refresh');
  return response.data;
};

// Admin APIs - Buses
export const getBuses = async () => {
  const response = await api.get('/api/admin/buses');
  return response.data;
};

export const getBus = async (id: number) => {
  const response = await api.get(`/api/admin/buses/${id}`);
  return response.data;
};

export const createBus = async (data: any) => {
  const response = await api.post('/api/admin/buses', data);
  return response.data;
};

export const updateBus = async (id: number, data: any) => {
  const response = await api.put(`/api/admin/buses/${id}`, data);
  return response.data;
};

export const deleteBus = async (id: number) => {
  await api.delete(`/api/admin/buses/${id}`);
};

// Admin APIs - Parents
export const getParents = async () => {
  const response = await api.get('/api/admin/parents');
  return response.data;
};

export const getParent = async (id: number) => {
  const response = await api.get(`/api/admin/parents/${id}`);
  return response.data;
};

export const createParent = async (data: any) => {
  const response = await api.post('/api/admin/parents', data);
  return response.data;
};

export const updateParent = async (id: number, data: any) => {
  const response = await api.put(`/api/admin/parents/${id}`, data);
  return response.data;
};

export const deleteParent = async (id: number) => {
  await api.delete(`/api/admin/parents/${id}`);
};

// Admin APIs - Students
export const getStudents = async (params?: { bus_id?: number; parent_id?: number }) => {
  const response = await api.get('/api/admin/students', { params });
  return response.data;
};

export const getStudent = async (id: number) => {
  const response = await api.get(`/api/admin/students/${id}`);
  return response.data;
};

export const createStudent = async (data: any, faceImage?: File) => {
  const formData = new FormData();
  Object.keys(data).forEach((key) => {
    formData.append(key, data[key]);
  });
  if (faceImage) {
    formData.append('face_image', faceImage);
  }
  const response = await api.post('/api/admin/students', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const updateStudent = async (id: number, data: any, faceImage?: File) => {
  const formData = new FormData();
  Object.keys(data).forEach((key) => {
    if (data[key] !== undefined) {
      formData.append(key, data[key]);
    }
  });
  if (faceImage) {
    formData.append('face_image', faceImage);
  }
  const response = await api.put(`/api/admin/students/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const deleteStudent = async (id: number) => {
  await api.delete(`/api/admin/students/${id}`);
};

// Admin APIs - GPS Trackers
export const getTrackers = async () => {
  const response = await api.get('/api/admin/trackers');
  return response.data;
};

export const createTracker = async (data: any) => {
  const response = await api.post('/api/admin/trackers', data);
  return response.data;
};

export const updateTracker = async (id: number, data: any) => {
  const response = await api.put(`/api/admin/trackers/${id}`, data);
  return response.data;
};

// Admin APIs - Settings
export const getSettings = async () => {
  const response = await api.get('/api/admin/settings');
  return response.data;
};

export const updateSettings = async (data: any) => {
  const response = await api.put('/api/admin/settings', data);
  return response.data;
};

// Admin APIs - Dashboard
export const getDashboardStats = async () => {
  const response = await api.get('/api/admin/dashboard/stats');
  return response.data;
};

// Parent APIs
export const getMyStudents = async () => {
  const response = await api.get('/api/parent/students');
  return response.data;
};

export const getMyStudent = async (id: number) => {
  const response = await api.get(`/api/parent/students/${id}`);
  return response.data;
};

export const getLastAttendance = async (studentId: number) => {
  const response = await api.get(`/api/parent/students/${studentId}/last-attendance`);
  return response.data;
};

export const getAttendanceHistory = async (studentId: number, params?: { start_date?: string; end_date?: string }) => {
  const response = await api.get(`/api/parent/students/${studentId}/attendance-history`, { params });
  return response.data;
};

export const getBusLocation = async (studentId: number) => {
  const response = await api.get(`/api/parent/students/${studentId}/bus-location`);
  return response.data;
};

export const getRouteHistory = async (studentId: number, params?: { start_time?: string; end_time?: string }) => {
  const response = await api.get(`/api/parent/students/${studentId}/route-history`, { params });
  return response.data;
};

// Legacy APIs (for backward compatibility)
export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getCameras = async () => {
  const response = await api.get('/api/cameras');
  return response.data;
};

export const getSavedImages = async (params?: {
  start_date?: string;
  end_date?: string;
  camera_ids?: string;
  page?: number;
  page_size?: number;
}) => {
  const response = await api.get('/api/saved_images', { params });
  return response.data;
};

export const searchByImage = async (formData: FormData) => {
  const response = await api.post('/api/search_by_image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Missing Report APIs (Public)
export const createMissingReport = async (formData: FormData) => {
  const response = await api.post('/api/reports/create', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const trackReport = async (phone: string, reportNumber: string) => {
  const response = await api.post('/api/reports/track', {
    phone,
    report_number: reportNumber,
  });
  return response.data;
};

export const closeReport = async (reportNumber: string, phone: string) => {
  const formData = new FormData();
  formData.append('phone', phone);
  const response = await api.post(`/api/reports/${reportNumber}/close`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Admin Report APIs (SystemUser Only)
export const getAllReports = async (params?: {
  page?: number;
  page_size?: number;
  status_filter?: string;
}) => {
  const response = await api.get('/api/admin/reports', { params });
  return response.data;
};

export const getReport = async (reportId: number) => {
  const response = await api.get(`/api/admin/reports/${reportId}`);
  return response.data;
};

export const updateReportStatus = async (reportId: number, status: string) => {
  const response = await api.put(`/api/admin/reports/${reportId}/status`, {
    status,
  });
  return response.data;
};

export const getReportMatches = async (reportId: number) => {
  const response = await api.get(`/api/admin/reports/${reportId}/matches`);
  return response.data;
};
