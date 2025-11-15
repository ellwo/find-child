import axios from 'axios';

// Get API base URL from environment or use relative path
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
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
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Authentication APIs
export const login = async (usernameOrEmail: string, password: string): Promise<{ access_token: string }> => {
  // Determine if input is email, phone, or username
  const isEmail = usernameOrEmail.includes('@');
  const isPhone = /^[\d+\-\s()]+$/.test(usernameOrEmail);
  
  const loginData: any = {
    password,
  };
  
  if (isEmail) {
    loginData.email = usernameOrEmail;
  } else if (isPhone) {
    loginData.phone = usernameOrEmail;
  } else {
    loginData.username = usernameOrEmail;
  }
  
  const response = await api.post('/api/auth/login', loginData);
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

export const getStudentTracking = async (id: number) => {
  const response = await api.get(`/api/admin/students/${id}/tracking`);
  return response.data;
};

export const getStudentAttendanceHistory = async (
  id: number,
  params?: { start_date?: string; end_date?: string; bus_id?: number; skip?: number; limit?: number }
) => {
  const response = await api.get(`/api/admin/students/${id}/attendance/history`, { params });
  return response.data;
};

export const createStudent = async (data: any, faceImage?: File) => {
  const formData = new FormData();
  Object.keys(data).forEach((key) => {
    const value = data[key];
    // Skip undefined, null, or empty string values (except for required fields)
    if (value !== undefined && value !== null && value !== '') {
      // Convert to string for form data
      if (typeof value === 'object') {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, String(value));
      }
    }
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
    const value = data[key];
    // Skip undefined, null, or empty string values (except for required fields)
    if (value !== undefined && value !== null && value !== '') {
      // Convert to string for form data
      if (typeof value === 'object') {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, String(value));
      }
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

// Admin APIs - Attendance Report
export const getAttendanceReport = async (params?: {
  start_date?: string;
  end_date?: string;
  bus_id?: number;
  student_id?: number;
  skip?: number;
  limit?: number;
}) => {
  const response = await api.get('/api/admin/reports/attendance', { params });
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
