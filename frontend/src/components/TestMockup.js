import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Button,
  Grid,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Paper,
  LinearProgress,
  Divider,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  ExpandMore,
  PlayArrow,
  Stop,
  CheckCircle,
  Error,
  Warning,
  Info,
  Refresh,
  Visibility,
  BugReport,
  Speed,
  Memory,
  Storage,
  NetworkCheck,
  Devices,
  LocationOn,
  Settings,
  Dashboard,
  Security,
  Analytics,
  Assessment,
  NotificationsActive,
  CloudUpload,
  QrCode,
  Lightbulb,
  Thermostat,
  DirectionsRun,
  PowerSettingsNew
} from '@mui/icons-material';
import { toast } from 'react-toastify';

// Import components to test
import EnhancedDeviceControl from './EnhancedDeviceControl';
import EnhancedDevicePairing from './EnhancedDevicePairing';
import ProvisioningManagement from './ProvisioningManagement';
import AdminDashboard from './AdminDashboard';
import UserDashboard from './Dashboard';
import ProductionTestRunner from './ProductionTestRunner';

// Mock data for testing
const mockDevices = [
  {
    id: 1,
    name: 'Living Room Smart Light',
    device_id: 'ESP32_001',
    device_type: { name: 'Smart Light' },
    location: { name: 'Living Room' },
    is_online: true,
    power_state: true,
    brightness: 75,
    supports_dimming: true,
    mac_address: 'AA:BB:CC:DD:EE:01',
    ip_address: '192.168.1.100',
    firmware_version: '1.0.0',
    last_seen: new Date().toISOString(),
    device_states: [
      { state_key: 'power', state_value: 'true' },
      { state_key: 'brightness', state_value: '75' }
    ]
  },
  {
    id: 2,
    name: 'Kitchen Temperature Sensor',
    device_id: 'ESP32_002',
    device_type: { name: 'Temperature Sensor' },
    location: { name: 'Kitchen' },
    is_online: true,
    power_state: false,
    mac_address: 'AA:BB:CC:DD:EE:02',
    ip_address: '192.168.1.101',
    firmware_version: '1.0.0',
    last_seen: new Date().toISOString(),
    device_states: [
      { state_key: 'temperature', state_value: '22.5' },
      { state_key: 'humidity', state_value: '45' }
    ]
  },
  {
    id: 3,
    name: 'Hallway Motion Sensor',
    device_id: 'ESP32_003',
    device_type: { name: 'Motion Sensor' },
    location: { name: 'Hallway' },
    is_online: false,
    power_state: false,
    mac_address: 'AA:BB:CC:DD:EE:03',
    ip_address: '192.168.1.102',
    firmware_version: '1.0.0',
    last_seen: new Date(Date.now() - 300000).toISOString(),
    device_states: [
      { state_key: 'motion', state_value: 'false' }
    ]
  },
  {
    id: 4,
    name: 'Bedroom Smart Switch',
    device_id: 'ESP32_004',
    device_type: { name: 'Smart Switch' },
    location: { name: 'Bedroom' },
    is_online: true,
    power_state: false,
    mac_address: 'AA:BB:CC:DD:EE:04',
    ip_address: '192.168.1.103',
    firmware_version: '1.0.0',
    last_seen: new Date().toISOString(),
    device_states: [
      { state_key: 'power', state_value: 'false' }
    ]
  }
];

const mockLocations = [
  { id: 1, name: 'Living Room', description: 'Main living area' },
  { id: 2, name: 'Kitchen', description: 'Cooking and dining area' },
  { id: 3, name: 'Bedroom', description: 'Master bedroom' },
  { id: 4, name: 'Hallway', description: 'Main hallway' }
];

const mockDeviceTypes = [
  { id: 1, name: 'Smart Light', description: 'LED smart bulb', capabilities: ['switch', 'dimming'] },
  { id: 2, name: 'Temperature Sensor', description: 'Temperature and humidity sensor', capabilities: ['sensor'] },
  { id: 3, name: 'Motion Sensor', description: 'PIR motion detector', capabilities: ['sensor'] },
  { id: 4, name: 'Smart Switch', description: 'Smart power switch', capabilities: ['switch'] }
];

const mockUsers = [
  { id: 1, username: 'admin', first_name: 'Admin', last_name: 'User', email: 'admin@example.com', is_active: true },
  { id: 2, username: 'user1', first_name: 'John', last_name: 'Doe', email: 'john@example.com', is_active: true },
  { id: 3, username: 'user2', first_name: 'Jane', last_name: 'Smith', email: 'jane@example.com', is_active: false }
];

const testScenarios = [
  {
    name: 'User Dashboard - Overview Tab',
    component: 'Dashboard',
    description: 'Test main dashboard with stats, device types, and locations',
    testCases: [
      'Display device statistics correctly',
      'Show online/offline device counts',
      'List device types with counts',
      'Display locations with device counts',
      'Show recent devices with status'
    ]
  },
  {
    name: 'Enhanced Device Control',
    component: 'EnhancedDeviceControl',
    description: 'Test real-time device control with emulator features',
    testCases: [
      'Real-time sensor readings display',
      'Interactive device controls (power, brightness)',
      'Live data charts with sensor trends',
      'Device configuration dialog',
      'ESP32 emulator integration'
    ]
  },
  {
    name: 'Device Pairing Wizard',
    component: 'EnhancedDevicePairing',
    description: 'Test 5-step device pairing process',
    testCases: [
      'Device scanning and discovery',
      'Device selection and details',
      'WiFi configuration setup',
      'Device-specific settings',
      'Final setup and validation'
    ]
  },
  {
    name: 'Provisioning Management',
    component: 'ProvisioningManagement',
    description: 'Test bulk device provisioning features',
    testCases: [
      'Batch creation and management',
      'QR code generation and display',
      'Device registration tracking',
      'CSV template download',
      'Batch status monitoring'
    ]
  },
  {
    name: 'Admin Dashboard',
    component: 'AdminDashboard',
    description: 'Test admin interface with all management features',
    testCases: [
      'User management interface',
      'Device management and control',
      'System analytics and metrics',
      'Firmware management',
      'ESP32 emulator integration'
    ]
  }
];

const TestMockup = () => {
  const [tabValue, setTabValue] = useState(0);
  const [testResults, setTestResults] = useState({});
  const [runningTests, setRunningTests] = useState(false);
  const [selectedTest, setSelectedTest] = useState(null);
  const [mockDataEnabled, setMockDataEnabled] = useState(true);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [currentTestComponent, setCurrentTestComponent] = useState(null);

  // Mock DeviceContext provider
  const mockDeviceContext = {
    devices: mockDevices,
    locations: mockLocations,
    deviceTypes: mockDeviceTypes,
    loading: false,
    fetchDevices: () => Promise.resolve(),
    sendDeviceCommand: () => Promise.resolve(),
    createDevice: () => Promise.resolve(),
    createLocation: () => Promise.resolve(),
    updateLocation: () => Promise.resolve(),
    deleteLocation: () => Promise.resolve()
  };

  // Mock AuthContext provider
  const mockAuthContext = {
    user: { first_name: 'Test', last_name: 'User', username: 'testuser' },
    isAdmin: () => true,
    isAuthenticated: true
  };

  useEffect(() => {
    // Initialize test results
    const initialResults = {};
    testScenarios.forEach(scenario => {
      initialResults[scenario.name] = {
        status: 'pending',
        results: scenario.testCases.map(testCase => ({
          name: testCase,
          status: 'pending',
          message: ''
        }))
      };
    });
    setTestResults(initialResults);
  }, []);

  const runTest = async (scenarioName) => {
    setRunningTests(true);
    const scenario = testScenarios.find(s => s.name === scenarioName);
    
    setTestResults(prev => ({
      ...prev,
      [scenarioName]: {
        ...prev[scenarioName],
        status: 'running'
      }
    }));

    // Simulate test execution
    for (let i = 0; i < scenario.testCases.length; i++) {
      const testCase = scenario.testCases[i];
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate test time
      
      const success = Math.random() > 0.2; // 80% success rate
      
      setTestResults(prev => ({
        ...prev,
        [scenarioName]: {
          ...prev[scenarioName],
          results: prev[scenarioName].results.map((result, index) => 
            index === i ? {
              ...result,
              status: success ? 'passed' : 'failed',
              message: success ? 'Test passed successfully' : 'Test failed - check implementation'
            } : result
          )
        }
      }));
    }

    setTestResults(prev => ({
      ...prev,
      [scenarioName]: {
        ...prev[scenarioName],
        status: 'completed'
      }
    }));

    setRunningTests(false);
    toast.success(`Test suite "${scenarioName}" completed`);
  };

  const runAllTests = async () => {
    setRunningTests(true);
    for (const scenario of testScenarios) {
      await runTest(scenario.name);
    }
    setRunningTests(false);
    toast.success('All tests completed!');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'passed': return <CheckCircle color="success" />;
      case 'failed': return <Error color="error" />;
      case 'running': return <Speed color="warning" />;
      default: return <Info color="info" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'passed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'warning';
      default: return 'info';
    }
  };

  const renderTestComponent = (componentName) => {
    const commonProps = {
      style: { transform: 'scale(0.8)', transformOrigin: 'top left' }
    };

    switch (componentName) {
      case 'Dashboard':
        return (
          <div style={{ ...commonProps, height: '600px', overflow: 'auto' }}>
            <UserDashboard />
          </div>
        );
      case 'EnhancedDeviceControl':
        return (
          <Grid container spacing={2}>
            {mockDevices.slice(0, 2).map(device => (
              <Grid item xs={12} md={6} key={device.id}>
                <EnhancedDeviceControl 
                  device={device} 
                  onUpdate={() => {}} 
                  {...commonProps}
                />
              </Grid>
            ))}
          </Grid>
        );
      case 'EnhancedDevicePairing':
        return (
          <Box sx={{ p: 2 }}>
            <Button
              variant="contained"
              onClick={() => setTestDialogOpen(true)}
            >
              Open Device Pairing Wizard
            </Button>
            <EnhancedDevicePairing
              open={testDialogOpen}
              onClose={() => setTestDialogOpen(false)}
              onDeviceAdded={() => {}}
            />
          </Box>
        );
      case 'ProvisioningManagement':
        return (
          <div style={{ ...commonProps, height: '600px', overflow: 'auto' }}>
            <ProvisioningManagement />
          </div>
        );
      case 'AdminDashboard':
        return (
          <div style={{ ...commonProps, height: '600px', overflow: 'auto' }}>
            <AdminDashboard />
          </div>
        );
      default:
        return <Typography>Component not found</Typography>;
    }
  };

  const renderTestResults = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Test Results</Typography>
        <Box>
          <FormControlLabel
            control={
              <Switch
                checked={mockDataEnabled}
                onChange={(e) => setMockDataEnabled(e.target.checked)}
              />
            }
            label="Use Mock Data"
          />
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={runAllTests}
            disabled={runningTests}
            sx={{ ml: 2 }}
          >
            Run All Tests
          </Button>
        </Box>
      </Box>

      {testScenarios.map((scenario) => (
        <Accordion key={scenario.name} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              {getStatusIcon(testResults[scenario.name]?.status)}
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6">{scenario.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {scenario.description}
                </Typography>
              </Box>
              <Button
                variant="outlined"
                size="small"
                startIcon={<PlayArrow />}
                onClick={(e) => {
                  e.stopPropagation();
                  runTest(scenario.name);
                }}
                disabled={runningTests}
              >
                Run Test
              </Button>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Test Cases
                </Typography>
                <List dense>
                  {testResults[scenario.name]?.results.map((result, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        {getStatusIcon(result.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={result.name}
                        secondary={result.message}
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Component Preview
                </Typography>
                <Paper 
                  sx={{ 
                    p: 2, 
                    height: '300px', 
                    overflow: 'auto',
                    border: '1px solid #e0e0e0'
                  }}
                >
                  {renderTestComponent(scenario.component)}
                </Paper>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );

  const renderSystemHealth = () => (
    <Box>
      <Typography variant="h6" gutterBottom>System Health Monitoring</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Memory sx={{ mr: 1 }} />
                Performance Metrics
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon><Speed /></ListItemIcon>
                  <ListItemText 
                    primary="Response Time" 
                    secondary={`${Math.round(Math.random() * 100 + 50)}ms`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Memory /></ListItemIcon>
                  <ListItemText 
                    primary="Memory Usage" 
                    secondary={`${Math.round(Math.random() * 30 + 40)}%`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><NetworkCheck /></ListItemIcon>
                  <ListItemText 
                    primary="Network Latency" 
                    secondary={`${Math.round(Math.random() * 20 + 10)}ms`}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <BugReport sx={{ mr: 1 }} />
                Error Monitoring
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon><Error color="error" /></ListItemIcon>
                  <ListItemText primary="Critical Errors" secondary="0" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Warning color="warning" /></ListItemIcon>
                  <ListItemText primary="Warnings" secondary="2" />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Info color="info" /></ListItemIcon>
                  <ListItemText primary="Info Messages" secondary="15" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  const renderMockDataManager = () => (
    <Box>
      <Typography variant="h6" gutterBottom>Mock Data Management</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Devices sx={{ mr: 1 }} />
                Devices ({mockDevices.length})
              </Typography>
              <List dense>
                {mockDevices.map(device => (
                  <ListItem key={device.id}>
                    <ListItemIcon>
                      {device.device_type.name === 'Smart Light' && <Lightbulb />}
                      {device.device_type.name === 'Temperature Sensor' && <Thermostat />}
                      {device.device_type.name === 'Motion Sensor' && <DirectionsRun />}
                      {device.device_type.name === 'Smart Switch' && <PowerSettingsNew />}
                    </ListItemIcon>
                    <ListItemText
                      primary={device.name}
                      secondary={
                        <Chip 
                          label={device.is_online ? 'Online' : 'Offline'} 
                          color={device.is_online ? 'success' : 'error'}
                          size="small"
                        />
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <LocationOn sx={{ mr: 1 }} />
                Locations ({mockLocations.length})
              </Typography>
              <List dense>
                {mockLocations.map(location => (
                  <ListItem key={location.id}>
                    <ListItemIcon><LocationOn /></ListItemIcon>
                    <ListItemText
                      primary={location.name}
                      secondary={location.description}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Security sx={{ mr: 1 }} />
                Users ({mockUsers.length})
              </Typography>
              <List dense>
                {mockUsers.map(user => (
                  <ListItem key={user.id}>
                    <ListItemIcon><Security /></ListItemIcon>
                    <ListItemText
                      primary={`${user.first_name} ${user.last_name}`}
                      secondary={
                        <Chip 
                          label={user.is_active ? 'Active' : 'Inactive'} 
                          color={user.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          🧪 Complete Application Test Mockup
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => window.location.reload()}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Chip
            label={mockDataEnabled ? 'Mock Data Enabled' : 'Live Data'}
            color={mockDataEnabled ? 'success' : 'warning'}
            icon={mockDataEnabled ? <CheckCircle /> : <Warning />}
          />
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body1">
          <strong>Test Environment:</strong> This mockup tests all application features including 
          Dashboard, Device Control, Pairing, Provisioning, and Admin interfaces. 
          Use mock data for consistent testing or switch to live data for integration testing.
        </Typography>
      </Alert>

      {runningTests && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Test Results" icon={<BugReport />} iconPosition="start" />
          <Tab label="Production Tests" icon={<Assessment />} iconPosition="start" />
          <Tab label="System Health" icon={<Analytics />} iconPosition="start" />
          <Tab label="Mock Data" icon={<Storage />} iconPosition="start" />
        </Tabs>
      </Box>

      {tabValue === 0 && renderTestResults()}
      {tabValue === 1 && <ProductionTestRunner />}
      {tabValue === 2 && renderSystemHealth()}
      {tabValue === 3 && renderMockDataManager()}
    </Container>
  );
};

export default TestMockup;