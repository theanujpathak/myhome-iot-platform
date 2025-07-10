import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People,
  Devices,
  Schedule,
  CloudUpload,
  Refresh,
  Edit,
  Delete,
  Block,
  CheckCircle,
  Error,
  Warning,
  Info,
  TrendingUp,
  Memory,
  Storage,
  Speed,
  Computer,
  Security,
  SettingsApplications,
  DeveloperBoard
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
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-toastify';
import DeviceTypes from './DeviceTypes';
import ProvisioningManagement from './ProvisioningManagement';
import EmulatedDeviceControl from './EmulatedDeviceControl';

const AdminDashboard = () => {
  const { isAdmin } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [systemStats, setSystemStats] = useState({});
  const [users, setUsers] = useState([]);
  const [devices, setDevices] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [firmwareList, setFirmwareList] = useState([]);
  const [deviceStatus, setDeviceStatus] = useState({});
  
  // Dialog states
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [firmwareDialogOpen, setFirmwareDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [firmwareFile, setFirmwareFile] = useState(null);
  const [firmwareData, setFirmwareData] = useState({
    version: '',
    device_type: '',
    description: ''
  });

  useEffect(() => {
    if (!isAdmin()) {
      return;
    }
    fetchAllData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, [isAdmin]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSystemStats(),
        fetchUsers(),
        fetchDevices(),
        fetchSchedules(),
        fetchAnalytics(),
        fetchFirmware(),
        fetchDeviceStatus()
      ]);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      toast.error('Failed to fetch admin data');
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemStats = async () => {
    try {
      const response = await axios.get('http://localhost:3003/api/analytics/system-stats');
      setSystemStats(response.data);
    } catch (error) {
      console.error('Error fetching system stats:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get('http://localhost:3001/api/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchDevices = async () => {
    try {
      const response = await axios.get('http://localhost:3002/api/devices');
      setDevices(response.data);
    } catch (error) {
      console.error('Error fetching devices:', error);
    }
  };

  const fetchSchedules = async () => {
    try {
      const response = await axios.get('http://localhost:3003/api/schedules');
      setSchedules(response.data);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    }
  };

  const fetchAnalytics = async () => {
    // Mock analytics data - in real implementation, this would come from analytics service
    const mockAnalytics = {
      deviceUsage: [
        { time: '00:00', lights: 20, switches: 15, sensors: 30 },
        { time: '06:00', lights: 80, switches: 60, sensors: 30 },
        { time: '12:00', lights: 60, switches: 45, sensors: 30 },
        { time: '18:00', lights: 90, switches: 70, sensors: 30 },
        { time: '23:00', lights: 40, switches: 25, sensors: 30 }
      ],
      systemMetrics: [
        { metric: 'CPU Usage', value: 45, max: 100, color: '#4caf50' },
        { metric: 'Memory', value: 68, max: 100, color: '#ff9800' },
        { metric: 'Storage', value: 32, max: 100, color: '#2196f3' },
        { metric: 'Network', value: 25, max: 100, color: '#9c27b0' }
      ],
      errorLogs: [
        { time: '2024-01-15 10:30', level: 'ERROR', service: 'Device Service', message: 'Device offline: smart_light_001' },
        { time: '2024-01-15 09:15', level: 'WARNING', service: 'Scheduler', message: 'Schedule execution delayed' },
        { time: '2024-01-15 08:45', level: 'INFO', service: 'User Service', message: 'New user registered' }
      ]
    };
    setAnalytics(mockAnalytics);
  };

  const fetchFirmware = async () => {
    try {
      const response = await axios.get('http://localhost:3004/api/firmware/list');
      setFirmwareList(response.data.firmware || []);
    } catch (error) {
      console.error('Error fetching firmware:', error);
    }
  };

  const fetchDeviceStatus = async () => {
    try {
      const response = await axios.get('http://localhost:3004/api/devices/status');
      setDeviceStatus(response.data.devices || {});
    } catch (error) {
      console.error('Error fetching device status:', error);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleUserAction = async (userId, action) => {
    try {
      if (action === 'disable') {
        // In real implementation, you'd call user management API
        toast.success('User disabled successfully');
      } else if (action === 'enable') {
        toast.success('User enabled successfully');
      }
      await fetchUsers();
    } catch (error) {
      toast.error('Failed to update user');
    }
  };

  const handleFirmwareUpload = async () => {
    if (!firmwareFile) {
      toast.error('Please select a firmware file');
      return;
    }

    const formData = new FormData();
    formData.append('file', firmwareFile);
    formData.append('version', firmwareData.version);
    formData.append('device_type', firmwareData.device_type);
    formData.append('description', firmwareData.description);

    try {
      await axios.post('http://localhost:3004/api/firmware/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast.success('Firmware uploaded successfully');
      setFirmwareDialogOpen(false);
      setFirmwareFile(null);
      setFirmwareData({ version: '', device_type: '', description: '' });
      await fetchFirmware();
    } catch (error) {
      toast.error('Failed to upload firmware');
    }
  };

  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      {/* System Metrics */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Metrics
            </Typography>
            {analytics.systemMetrics?.map((metric) => (
              <Box key={metric.metric} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">{metric.metric}</Typography>
                  <Typography variant="body2">{metric.value}%</Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={metric.value}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#f0f0f0',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: metric.color
                    }
                  }}
                />
              </Box>
            ))}
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Stats */}
      <Grid item xs={12} md={6}>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <People sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4">{users.length}</Typography>
                <Typography variant="body2" color="text.secondary">Total Users</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Devices sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4">{devices.length}</Typography>
                <Typography variant="body2" color="text.secondary">Total Devices</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Schedule sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant="h4">{systemStats.schedules?.total || 0}</Typography>
                <Typography variant="body2" color="text.secondary">Schedules</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <TrendingUp sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                <Typography variant="h4">{Math.round(systemStats.executions?.success_rate || 0)}%</Typography>
                <Typography variant="body2" color="text.secondary">Success Rate</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Grid>

      {/* Device Usage Chart */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Device Usage Over Time
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics.deviceUsage}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="lights" stroke="#4caf50" strokeWidth={2} />
                <Line type="monotone" dataKey="switches" stroke="#2196f3" strokeWidth={2} />
                <Line type="monotone" dataKey="sensors" stroke="#ff9800" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Recent System Logs */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent System Logs
            </Typography>
            <List>
              {analytics.errorLogs?.map((log, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    {log.level === 'ERROR' && <Error color="error" />}
                    {log.level === 'WARNING' && <Warning color="warning" />}
                    {log.level === 'INFO' && <Info color="info" />}
                  </ListItemIcon>
                  <ListItemText
                    primary={log.message}
                    secondary={`${log.time} - ${log.service}`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderUsersTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6">User Management</Typography>
        <Button
          variant="contained"
          startIcon={<People />}
          onClick={() => setUserDialogOpen(true)}
        >
          Add User
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ mr: 2 }}>
                      {(user.first_name || user.username || 'U').charAt(0).toUpperCase()}
                    </Avatar>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        {user.first_name} {user.last_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        @{user.username}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <Chip
                    label={user.is_active ? 'Active' : 'Inactive'}
                    color={user.is_active ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => setSelectedUser(user)}
                  >
                    <Edit />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleUserAction(user.id, user.is_active ? 'disable' : 'enable')}
                  >
                    {user.is_active ? <Block /> : <CheckCircle />}
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderDevicesTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>Device Management</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Device</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Firmware</TableCell>
                  <TableCell>Last Seen</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {devices.map((device) => {
                  const status = deviceStatus[device.device_id] || {};
                  return (
                    <TableRow key={device.id}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {device.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {device.device_id}
                        </Typography>
                      </TableCell>
                      <TableCell>{device.device_type?.name}</TableCell>
                      <TableCell>
                        <Chip
                          label={device.is_online ? 'Online' : 'Offline'}
                          color={device.is_online ? 'success' : 'error'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {status.current_version || device.firmware_version || 'Unknown'}
                      </TableCell>
                      <TableCell>
                        {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                      </TableCell>
                      <TableCell>
                        <IconButton size="small">
                          <Edit />
                        </IconButton>
                        <IconButton size="small">
                          <CloudUpload />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Device Statistics</Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">Online Devices</Typography>
                <Typography variant="h4" color="success.main">
                  {devices.filter(d => d.is_online).length}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2">Offline Devices</Typography>
                <Typography variant="h4" color="error.main">
                  {devices.filter(d => !d.is_online).length}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2">Total Devices</Typography>
                <Typography variant="h4" color="primary.main">
                  {devices.length}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  const renderFirmwareTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6">Firmware Management</Typography>
        <Button
          variant="contained"
          startIcon={<CloudUpload />}
          onClick={() => setFirmwareDialogOpen(true)}
        >
          Upload Firmware
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Filename</TableCell>
              <TableCell>Version</TableCell>
              <TableCell>Device Type</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Upload Date</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {firmwareList.map((firmware) => (
              <TableRow key={firmware.filename}>
                <TableCell>{firmware.filename}</TableCell>
                <TableCell>{firmware.version}</TableCell>
                <TableCell>{firmware.device_type}</TableCell>
                <TableCell>{Math.round(firmware.file_size / 1024)} KB</TableCell>
                <TableCell>
                  {new Date(firmware.upload_time).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <IconButton size="small">
                    <CloudUpload />
                  </IconButton>
                  <IconButton size="small">
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  if (!isAdmin()) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">
          Access denied. Administrator privileges required.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Admin Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchAllData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Overview" icon={<DashboardIcon />} />
          <Tab label="Users" icon={<People />} />
          <Tab label="Devices" icon={<Devices />} />
          <Tab label="Device Types" icon={<Devices />} />
          <Tab label="Provisioning" icon={<SettingsApplications />} />
          <Tab label="ESP32 Emulator" icon={<DeveloperBoard />} />
          <Tab label="Firmware" icon={<CloudUpload />} />
        </Tabs>
      </Box>

      <Box sx={{ mt: 3 }}>
        {tabValue === 0 && renderOverviewTab()}
        {tabValue === 1 && renderUsersTab()}
        {tabValue === 2 && renderDevicesTab()}
        {tabValue === 3 && <DeviceTypes />}
        {tabValue === 4 && <ProvisioningManagement />}
        {tabValue === 5 && <EmulatedDeviceControl />}
        {tabValue === 6 && renderFirmwareTab()}
      </Box>

      {/* Firmware Upload Dialog */}
      <Dialog
        open={firmwareDialogOpen}
        onClose={() => setFirmwareDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload Firmware</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <input
              type="file"
              accept=".bin"
              onChange={(e) => setFirmwareFile(e.target.files[0])}
              style={{ width: '100%', padding: '10px', marginTop: '10px' }}
            />
          </Box>
          
          <TextField
            fullWidth
            label="Version"
            value={firmwareData.version}
            onChange={(e) => setFirmwareData({ ...firmwareData, version: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Device Type</InputLabel>
            <Select
              value={firmwareData.device_type}
              onChange={(e) => setFirmwareData({ ...firmwareData, device_type: e.target.value })}
              label="Device Type"
            >
              <MenuItem value="Smart Light">Smart Light</MenuItem>
              <MenuItem value="Smart Switch">Smart Switch</MenuItem>
              <MenuItem value="Temperature Sensor">Temperature Sensor</MenuItem>
              <MenuItem value="Smart Plug">Smart Plug</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={3}
            value={firmwareData.description}
            onChange={(e) => setFirmwareData({ ...firmwareData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFirmwareDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleFirmwareUpload} variant="contained">Upload</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminDashboard;