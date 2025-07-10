import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import keycloak from './keycloak';
import LoadingSpinner from './components/LoadingSpinner';
import axios from 'axios';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import DeviceControl from './components/DeviceControl';
import Schedule from './components/Schedule';
import Profile from './components/Profile';
import AdminDashboard from './components/AdminDashboard';
import HealthDashboard from './components/HealthDashboard';
import Layout from './components/Layout';
import TestMockup from './components/TestMockup';
import { AuthProvider } from './contexts/AuthContext';
import { DeviceProvider } from './contexts/DeviceContext';
import { NotificationProvider } from './contexts/NotificationContext';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  const [keycloakInitialized, setKeycloakInitialized] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if Keycloak is already initialized
    if (window.keycloakInitialized) {
      setAuthenticated(keycloak.authenticated || false);
      setKeycloakInitialized(true);
      setLoading(false);
      return;
    }

    // Initialize Keycloak only once
    keycloak
      .init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        checkLoginIframe: false,
        pkceMethod: 'S256',
      })
      .then((authenticated) => {
        window.keycloakInitialized = true;
        setAuthenticated(authenticated);
        setKeycloakInitialized(true);
        setLoading(false);
        
        if (authenticated) {
          console.log('User is authenticated');
          // Set up token refresh only once
          if (!window.tokenRefreshInterval) {
            window.tokenRefreshInterval = setInterval(() => {
              keycloak.updateToken(30).then((refreshed) => {
                if (refreshed) {
                  console.log('Token refreshed');
                  // Update axios headers with new token
                  axios.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`;
                }
              }).catch(() => {
                console.log('Failed to refresh token');
              });
            }, 30000);
          }
        }
      })
      .catch((error) => {
        console.error('Keycloak initialization failed:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!keycloakInitialized) {
    return <div>Failed to initialize authentication</div>;
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider keycloak={keycloak}>
        <DeviceProvider>
          <NotificationProvider>
            <Router>
            <div className="App">
              {authenticated ? (
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/devices" element={<DeviceControl />} />
                    <Route path="/health" element={<HealthDashboard />} />
                    <Route path="/schedule" element={<Schedule />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/admin" element={<AdminDashboard />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </Layout>
              ) : (
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route path="*" element={<Navigate to="/login" replace />} />
                </Routes>
              )}
            </div>
            </Router>
          </NotificationProvider>
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
          />
        </DeviceProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;