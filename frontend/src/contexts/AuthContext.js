import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children, keycloak }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (keycloak.authenticated) {
      // Set up axios defaults
      axios.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`;
      
      // Set up axios interceptor to always include the latest token
      const requestInterceptor = axios.interceptors.request.use(
        (config) => {
          if (keycloak.token) {
            config.headers.Authorization = `Bearer ${keycloak.token}`;
          }
          return config;
        },
        (error) => {
          return Promise.reject(error);
        }
      );
      
      // Set up response interceptor to handle 401/403 errors
      const responseInterceptor = axios.interceptors.response.use(
        (response) => response,
        async (error) => {
          if (error.response?.status === 401 || error.response?.status === 403) {
            try {
              // Try to refresh token
              await keycloak.updateToken(5);
              // Update axios headers with new token
              axios.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`;
              // Retry the original request
              error.config.headers.Authorization = `Bearer ${keycloak.token}`;
              return axios.request(error.config);
            } catch (refreshError) {
              console.error('Token refresh failed:', refreshError);
              keycloak.logout();
              return Promise.reject(error);
            }
          }
          return Promise.reject(error);
        }
      );
      
      // Fetch user profile
      fetchUserProfile();
      
      // Cleanup interceptors on unmount
      return () => {
        axios.interceptors.request.eject(requestInterceptor);
        axios.interceptors.response.eject(responseInterceptor);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [keycloak.authenticated]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get('/api/user/profile');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = () => {
    keycloak.login();
  };

  const logout = () => {
    keycloak.logout();
  };

  const hasRole = (role) => {
    return keycloak.hasRealmRole(role);
  };

  const isAdmin = () => {
    return hasRole('admin');
  };

  const isManager = () => {
    return hasRole('manager');
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await axios.put('/api/user/profile', profileData);
      setUser(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    }
  };

  const value = {
    user,
    loading,
    authenticated: keycloak.authenticated,
    login,
    logout,
    hasRole,
    isAdmin,
    isManager,
    updateProfile,
    keycloak,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};