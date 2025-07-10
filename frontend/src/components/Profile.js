import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Avatar,
  Grid,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip
} from '@mui/material';
import {
  Person,
  Email,
  Security,
  Save,
  Lock,
  AdminPanelSettings,
  Group,
  AccessTime
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Profile = () => {
  const { user, updateProfile, isAdmin, isManager } = useAuth();
  const [profileForm, setProfileForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    username: user?.username || ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await updateProfile(profileForm);
      setMessage('Profile updated successfully!');
    } catch (error) {
      setMessage('Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getUserRoles = () => {
    const roles = [];
    if (isAdmin()) roles.push({ name: 'Administrator', color: 'error', icon: <AdminPanelSettings /> });
    if (isManager()) roles.push({ name: 'Manager', color: 'warning', icon: <Group /> });
    roles.push({ name: 'User', color: 'primary', icon: <Person /> });
    return roles;
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Profile Settings
      </Typography>

      {message && (
        <Alert 
          severity={message.includes('success') ? 'success' : 'error'} 
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Avatar
                sx={{ 
                  width: 120, 
                  height: 120, 
                  mx: 'auto', 
                  mb: 2,
                  bgcolor: 'primary.main',
                  fontSize: '3rem'
                }}
              >
                {(user?.first_name || user?.username || 'U').charAt(0).toUpperCase()}
              </Avatar>
              <Typography variant="h5" gutterBottom>
                {user?.first_name} {user?.last_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                @{user?.username}
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                {getUserRoles().map((role, index) => (
                  <Chip
                    key={role.name}
                    icon={role.icon}
                    label={role.name}
                    color={role.color}
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Information
              </Typography>
              <List>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <Email />
                  </ListItemIcon>
                  <ListItemText
                    primary="Email"
                    secondary={user?.email}
                  />
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <AccessTime />
                  </ListItemIcon>
                  <ListItemText
                    primary="Member Since"
                    secondary={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                  />
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <Security />
                  </ListItemIcon>
                  <ListItemText
                    primary="Authentication"
                    secondary="SSO (Keycloak)"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Personal Information
              </Typography>
              <Box component="form" onSubmit={handleProfileUpdate}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={profileForm.first_name}
                      onChange={(e) => setProfileForm({ 
                        ...profileForm, 
                        first_name: e.target.value 
                      })}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={profileForm.last_name}
                      onChange={(e) => setProfileForm({ 
                        ...profileForm, 
                        last_name: e.target.value 
                      })}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Username"
                      value={profileForm.username}
                      onChange={(e) => setProfileForm({ 
                        ...profileForm, 
                        username: e.target.value 
                      })}
                      margin="normal"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Email"
                      value={user?.email || ''}
                      disabled
                      margin="normal"
                      helperText="Email cannot be changed. Contact administrator if needed."
                    />
                  </Grid>
                </Grid>
                
                <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={<Save />}
                    disabled={loading}
                  >
                    {loading ? 'Saving...' : 'Save Changes'}
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Security Settings
              </Typography>
              <Alert severity="info" sx={{ mb: 2 }}>
                Security settings are managed through the SSO system. Use the links below to manage your account security.
              </Alert>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<Lock />}
                  onClick={() => window.open('http://localhost:8080/realms/home-automation/account', '_blank')}
                >
                  Change Password
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Security />}
                  onClick={() => window.open('http://localhost:8080/realms/home-automation/account/security/signingin', '_blank')}
                >
                  Two-Factor Authentication
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<AccessTime />}
                  onClick={() => window.open('http://localhost:8080/realms/home-automation/account/security/sessions', '_blank')}
                >
                  Active Sessions
                </Button>
              </Box>
            </CardContent>
          </Card>

          {isAdmin() && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Administrator Tools
                </Typography>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  You have administrator privileges. Use these tools responsibly.
                </Alert>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={() => window.open('http://localhost:8080/admin/master/console/#/home-automation', '_blank')}
                  >
                    Keycloak Admin Console
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => console.log('System settings')}
                  >
                    System Settings
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => console.log('User management')}
                  >
                    User Management
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Profile;