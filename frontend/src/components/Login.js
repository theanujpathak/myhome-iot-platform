import React from 'react';
import { 
  Container, 
  Paper, 
  Typography, 
  Button, 
  Box,
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import { Home, Security, Devices, Schedule } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const { login } = useAuth();

  return (
    <Container maxWidth="md" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
        <Box sx={{ mb: 4 }}>
          <Home sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h3" component="h1" gutterBottom>
            Home Automation System
          </Typography>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Secure, Smart, and Simple
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 4 }}>
          <Card sx={{ minWidth: 200, textAlign: 'center' }}>
            <CardContent>
              <Devices sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6">
                Device Control
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Control all your smart home devices from one place
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ minWidth: 200, textAlign: 'center' }}>
            <CardContent>
              <Schedule sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6">
                Smart Scheduling
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Automate your home with intelligent scheduling
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ minWidth: 200, textAlign: 'center' }}>
            <CardContent>
              <Security sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h6">
                Secure Access
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Enterprise-grade security with SSO integration
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ mb: 4 }}>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            Welcome to your smart home management system. Sign in to access your devices,
            create schedules, and manage your home automation settings.
          </Typography>
        </Box>

        <Box>
          <Button
            variant="contained"
            size="large"
            onClick={login}
            sx={{ 
              px: 4, 
              py: 2, 
              fontSize: '1.1rem',
              borderRadius: 2,
              textTransform: 'none'
            }}
          >
            Sign In with SSO
          </Button>
        </Box>

        <Box sx={{ mt: 4, p: 2, backgroundColor: 'grey.50', borderRadius: 2 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>Demo Credentials:</strong><br />
            Admin: admin / admin123<br />
            Manager: manager / manager123<br />
            User: user / user123
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default Login;