import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add JWT token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor to handle unauthorized errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if we received a 401 and we haven't already retried this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const token = localStorage.getItem('token');
        const authStorage = localStorage.getItem('auth-storage');
        let role = 'patient'; // Default
        
        if (authStorage) {
          try {
            const parsed = JSON.parse(authStorage);
            role = parsed?.state?.user?.role || 'patient';
          } catch (e) {
            console.error("Failed to parse auth storage", e);
          }
        }
        
        // Determine the correct refresh endpoint based on the user's role
        const refreshEndpoint = role === 'patient' ? '/users/refresh' : '/auth/refresh';
        
        const res = await axios.post(`${API_URL}${refreshEndpoint}`, { token });
        
        if (res.data && res.data.access_token) {
          const newToken = res.data.access_token;
          
          // Save the new token in localStorage
          localStorage.setItem('token', newToken);
          
          // Update the zustand auth storage if possible
          if (authStorage) {
            try {
              const parsed = JSON.parse(authStorage);
              parsed.state.token = newToken;
              localStorage.setItem('auth-storage', JSON.stringify(parsed));
            } catch (e) {
               // ignore
            }
          }
          
          // Update the authorization header for the original request
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          
          // Retry the original request
          return axios(originalRequest);
        }
      } catch (refreshError) {
        // If refresh fails, and it's from the AI chat, don't auto-logout
        if (originalRequest.url?.includes('/chat')) {
          return Promise.reject({
            ...error,
            message: "AI service temporarily unavailable - Auth failed"
          });
        }
        
        // Ensure complete logout on refresh failure
        localStorage.removeItem('token');
        localStorage.removeItem('auth-storage');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }
    
    // Prevent auto-logout if the initial error came from the AI chat (and not handled by retry)
    if (error.response?.status === 401 && originalRequest.url?.includes('/chat')) {
      return Promise.reject({
        ...error,
        message: "AI service temporarily unavailable - Auth failed"
      });
    }

    // Default 401 handler if not a retry flow
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('auth-storage');
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
