import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemAvatar,
  Avatar,
  Tabs,
  Tab,
  Alert,
  Divider,
  Paper
} from '@mui/material';
import {
  FavoriteOutlined,
  DirectionsRun,
  MonitorWeight,
  Bloodtype,
  Bedtime,
  Air,
  LocalHospital,
  TrendingUp,
  TrendingDown,
  Remove,
  Refresh,
  Timeline,
  Assessment,
  CalendarToday,
  Speed
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useDevices } from '../contexts/DeviceContext';
import { useAuth } from '../contexts/AuthContext';
import HealthDevicePairing from './HealthDevicePairing';

const HealthDashboard = () => {
  const { user } = useAuth();
  const { devices, loading } = useDevices();
  const [tabValue, setTabValue] = useState(0);
  const [healthPairingOpen, setHealthPairingOpen] = useState(false);
  
  // Filter health devices
  const healthDevices = devices.filter(device => {
    const healthCategories = [
      'Fitness Tracker', 'Health Monitor', 'Smart Scale', 
      'Blood Pressure Monitor', 'Sleep Tracker', 'Air Quality Monitor', 
      'Medical Alert Device'
    ];
    return healthCategories.includes(device.device_type?.name);
  });

  // Mock health data - in real implementation, this would come from the backend
  const mockHealthMetrics = {
    todayStats: {
      steps: 8450,
      heartRate: 72,
      weight: 68.5,
      sleepHours: 7.5,
      activeMinutes: 45
    },
    weeklyData: [
      { day: 'Mon', steps: 8200, heartRate: 70, sleepHours: 7.8 },
      { day: 'Tue', steps: 9100, heartRate: 68, sleepHours: 7.2 },
      { day: 'Wed', steps: 7800, heartRate: 74, sleepHours: 8.1 },
      { day: 'Thu', steps: 8450, heartRate: 72, sleepHours: 7.5 },
      { day: 'Fri', steps: 9200, heartRate: 69, sleepHours: 7.0 },
      { day: 'Sat', steps: 10100, heartRate: 71, sleepHours: 8.5 },
      { day: 'Sun', steps: 6800, heartRate: 73, sleepHours: 8.2 }
    ],
    goals: {
      steps: { current: 8450, target: 10000 },
      activeMinutes: { current: 45, target: 60 },
      sleepHours: { current: 7.5, target: 8.0 }
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const getHealthIcon = (category) => {
    switch (category) {
      case 'Fitness Tracker':
        return <DirectionsRun />;
      case 'Health Monitor':
        return <FavoriteOutlined />;
      case 'Smart Scale':
        return <MonitorWeight />;
      case 'Blood Pressure Monitor':
        return <Bloodtype />;
      case 'Sleep Tracker':
        return <Bedtime />;
      case 'Air Quality Monitor':
        return <Air />;
      case 'Medical Alert Device':
        return <LocalHospital />;
      default:
        return <FavoriteOutlined />;
    }
  };

  const getTrendIcon = (current, target) => {
    if (current >= target) return <TrendingUp color="success" />;
    if (current >= target * 0.8) return <Remove color="warning" />;
    return <TrendingDown color="error" />;
  };

  const getProgressColor = (current, target) => {
    const percentage = (current / target) * 100;
    if (percentage >= 100) return 'success';
    if (percentage >= 80) return 'warning';
    return 'error';
  };

  const renderOverviewTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Health Overview for {user?.first_name || user?.username}
      </Typography>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {healthDevices.length === 0 ? (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          action={
            <Button 
              color="primary" 
              size="small"
              onClick={() => setHealthPairingOpen(true)}
            >
              Add Health Device
            </Button>
          }
        >
          No health devices found. Add your first health device to start tracking your wellness data.
        </Alert>
      ) : (
        <>
          {/* Today's Stats */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <DirectionsRun sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="h4" color="primary">
                    {mockHealthMetrics.todayStats.steps.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Steps Today</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(mockHealthMetrics.todayStats.steps / mockHealthMetrics.goals.steps.target) * 100}
                    color={getProgressColor(mockHealthMetrics.todayStats.steps, mockHealthMetrics.goals.steps.target)}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <FavoriteOutlined sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
                  <Typography variant="h4" color="error.main">
                    {mockHealthMetrics.todayStats.heartRate}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Heart Rate (BPM)</Typography>
                  <Typography variant="caption" color="success.main">Normal Range</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <MonitorWeight sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                  <Typography variant="h4" color="info.main">
                    {mockHealthMetrics.todayStats.weight}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Weight (kg)</Typography>
                  <Typography variant="caption" color="success.main">Healthy BMI</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Bedtime sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                  <Typography variant="h4" color="secondary.main">
                    {mockHealthMetrics.todayStats.sleepHours}h
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Sleep Last Night</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(mockHealthMetrics.todayStats.sleepHours / mockHealthMetrics.goals.sleepHours.target) * 100}
                    color={getProgressColor(mockHealthMetrics.todayStats.sleepHours, mockHealthMetrics.goals.sleepHours.target)}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={2.4}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Speed sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h4" color="warning.main">
                    {mockHealthMetrics.todayStats.activeMinutes}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Active Minutes</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(mockHealthMetrics.todayStats.activeMinutes / mockHealthMetrics.goals.activeMinutes.target) * 100}
                    color={getProgressColor(mockHealthMetrics.todayStats.activeMinutes, mockHealthMetrics.goals.activeMinutes.target)}
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Weekly Trends Chart */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Weekly Activity Trends
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={mockHealthMetrics.weeklyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="steps" 
                        stroke="#1976d2" 
                        strokeWidth={2}
                        name="Steps"
                      />
                      <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="heartRate" 
                        stroke="#d32f2f" 
                        strokeWidth={2}
                        name="Heart Rate (BPM)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Daily Goals
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon>
                        {getTrendIcon(mockHealthMetrics.goals.steps.current, mockHealthMetrics.goals.steps.target)}
                      </ListItemIcon>
                      <ListItemText
                        primary="Steps"
                        secondary={`${mockHealthMetrics.goals.steps.current.toLocaleString()} / ${mockHealthMetrics.goals.steps.target.toLocaleString()}`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        {getTrendIcon(mockHealthMetrics.goals.activeMinutes.current, mockHealthMetrics.goals.activeMinutes.target)}
                      </ListItemIcon>
                      <ListItemText
                        primary="Active Minutes"
                        secondary={`${mockHealthMetrics.goals.activeMinutes.current} / ${mockHealthMetrics.goals.activeMinutes.target} min`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        {getTrendIcon(mockHealthMetrics.goals.sleepHours.current, mockHealthMetrics.goals.sleepHours.target)}
                      </ListItemIcon>
                      <ListItemText
                        primary="Sleep"
                        secondary={`${mockHealthMetrics.goals.sleepHours.current} / ${mockHealthMetrics.goals.sleepHours.target} hours`}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );

  const renderDevicesTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Health Devices</Typography>
        <Button
          variant="contained"
          startIcon={<FavoriteOutlined />}
          onClick={() => setHealthPairingOpen(true)}
        >
          Add Health Device
        </Button>
      </Box>

      {healthDevices.length === 0 ? (
        <Alert severity="info">
          No health devices configured. Add your first health device to start monitoring your wellness data.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {healthDevices.map((device) => (
            <Grid item xs={12} md={6} lg={4} key={device.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                      {getHealthIcon(device.device_type?.name)}
                    </Avatar>
                    <Box>
                      <Typography variant="h6">{device.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {device.device_type?.name}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body2">Status</Typography>
                    <Chip
                      label={device.is_online ? 'Connected' : 'Disconnected'}
                      color={device.is_online ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body2">Last Sync</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {device.last_seen ? new Date(device.last_seen).toLocaleTimeString() : 'Never'}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 1 }} />
                  
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                    {(device.device_type?.capabilities || []).map((capability) => (
                      <Chip
                        key={capability}
                        label={capability.replace('_', ' ')}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                    <Button size="small" startIcon={<Timeline />}>
                      View Data
                    </Button>
                    <IconButton size="small">
                      <Refresh />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  const renderAnalyticsTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Health Analytics
      </Typography>
      
      {healthDevices.length === 0 ? (
        <Alert severity="info">
          Add health devices to view detailed analytics and insights.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Sleep Quality Trends
                </Typography>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={mockHealthMetrics.weeklyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="sleepHours" 
                      stroke="#9c27b0" 
                      fill="#9c27b0" 
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Weekly Summary
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Average Steps"
                      secondary={`${Math.round(mockHealthMetrics.weeklyData.reduce((sum, day) => sum + day.steps, 0) / 7).toLocaleString()} steps/day`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Average Heart Rate"
                      secondary={`${Math.round(mockHealthMetrics.weeklyData.reduce((sum, day) => sum + day.heartRate, 0) / 7)} BPM`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Average Sleep"
                      secondary={`${(mockHealthMetrics.weeklyData.reduce((sum, day) => sum + day.sleepHours, 0) / 7).toFixed(1)} hours/night`}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Goals Achieved"
                      secondary="3 out of 7 days"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Health Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={() => window.location.reload()}
        >
          Refresh
        </Button>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab 
            label="Overview" 
            icon={<Assessment />} 
            iconPosition="start"
          />
          <Tab 
            label="Devices" 
            icon={<FavoriteOutlined />} 
            iconPosition="start"
          />
          <Tab 
            label="Analytics" 
            icon={<Timeline />} 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {tabValue === 0 && renderOverviewTab()}
      {tabValue === 1 && renderDevicesTab()}
      {tabValue === 2 && renderAnalyticsTab()}

      {/* Health Device Pairing Dialog */}
      <HealthDevicePairing
        open={healthPairingOpen}
        onClose={() => setHealthPairingOpen(false)}
        onDeviceAdded={() => window.location.reload()}
      />
    </Container>
  );
};

export default HealthDashboard;