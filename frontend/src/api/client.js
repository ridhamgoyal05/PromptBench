import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE_URL,
});

// Memory token store with localStorage backup
let inMemoryToken = '';

export const setAuthToken = (token) => {
  inMemoryToken = token;
  if (token) {
    try {
      localStorage.setItem('token', token);
    } catch (e) {
      // Silently catch if localStorage is blocked in sandboxed browsers
    }
  } else {
    try {
      localStorage.removeItem('token');
    } catch (e) {
      // Catch error
    }
  }
};

export const getAuthToken = () => {
  if (inMemoryToken) return inMemoryToken;
  try {
    return localStorage.getItem('token') || '';
  } catch (e) {
    return '';
  }
};

client.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default client;
