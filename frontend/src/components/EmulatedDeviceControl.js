import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
  Chip,
  Slider,
  Switch,
  FormControlLabel,
  Alert,
  LinearProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  Fab,
  Badge
} from '@mui/material';
import {
  Lightbulb,
  PowerOutlined,
  Thermostat,
  DirectionsRun,
  MeetingRoom,
  Refresh,
  Settings,
  Visibility,
  PowerOff,
  Power,
  Speed,
  SignalWifi4Bar,
  Battery3Bar,
  WifiOff,
  Wifi
} from '@mui/icons-material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import axios from 'axios';
import { toast } from 'react-toastify';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend
);

const EmulatedDeviceControl = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [sensorData, setSensorData] = useState({});
  const [autoRefresh, setAutoRefresh] = useState(true);

  const emulatorUrl = 'http://localhost:8090';

  useEffect(() => {
    fetchDevices();
    
    if (autoRefresh) {
      const interval = setInterval(fetchDevices, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${emulatorUrl}/api/devices`);
      setDevices(response.data);
      
      // Update sensor data for charts
      const newSensorData = {};
      response.data.forEach(device => {
        if (device.device_type === 'Temperature Sensor') {
          if (!sensorData[device.device_id]) {
            newSensorData[device.device_id] = {
              labels: [],
              temperature: [],
              humidity: []
            };
          } else {
            newSensorData[device.device_id] = { ...sensorData[device.device_id] };
          }
          
          const now = new Date().toLocaleTimeString();
          newSensorData[device.device_id].labels.push(now);
          newSensorData[device.device_id].temperature.push(device.temperature);
          newSensorData[device.device_id].humidity.push(device.humidity);
          
          // Keep only last 20 data points
          if (newSensorData[device.device_id].labels.length > 20) {
            newSensorData[device.device_id].labels.shift();
            newSensorData[device.device_id].temperature.shift();
            newSensorData[device.device_id].humidity.shift();
          }
        }
      });
      
      setSensorData(prev => ({ ...prev, ...newSensorData }));
      
    } catch (error) {
      console.error('Failed to fetch devices:', error);
      toast.error('Failed to connect to ESP32 emulator. Make sure it\'s running on port 8090.');
    } finally {
      setLoading(false);
    }
  };

  const controlDevice = async (deviceId, controlData) => {
    try {
      const response = await axios.post(
        `${emulatorUrl}/api/devices/${deviceId}/control`,
        controlData
      );
      
      if (response.data.success) {
        toast.success(`Device ${deviceId} controlled successfully`);
        // Update the device in our local state
        setDevices(prevDevices => 
          prevDevices.map(device => 
            device.device_id === deviceId 
              ? { ...device, ...response.data.device }
              : device
          )
        );
      }
    } catch (error) {
      console.error('Failed to control device:', error);
      toast.error(`Failed to control device ${deviceId}`);
    }
  };

  const togglePower = (deviceId, currentState) => {
    controlDevice(deviceId, { power_state: !currentState });
  };

  const setBrightness = (deviceId, brightness) => {
    controlDevice(deviceId, { brightness });
  };

  const simulateSensor = async (deviceId) => {
    try {
      // This would trigger sensor simulation via WebSocket if connected
      // For now, we'll just refresh the device data
      await fetchDevices();
      toast.info(`Sensor simulation triggered for ${deviceId}`);
    } catch (error) {
      toast.error('Failed to simulate sensor');
    }
  };

  const getDeviceIcon = (deviceType) => {
    switch (deviceType) {
      case 'Smart Light': return <Lightbulb />;
      case 'Smart Switch': return <PowerOutlined />;
      case 'Temperature Sensor': return <Thermostat />;
      case 'Motion Sensor': return <DirectionsRun />;
      case 'Door Sensor': return <MeetingRoom />;
      default: return <Settings />;
    }
  };

  const getStatusColor = (device) => {
    if (!device.is_online) return 'error';
    if (device.power_state) return 'success';
    return 'default';
  };

  const renderDeviceCard = (device) => (
    <Grid item xs={12} md={6} lg={4} key={device.device_id}>
      <Card 
        sx={{ 
          height: '100%',
          border: device.power_state ? '2px solid #4caf50' : '1px solid #ddd',
          boxShadow: device.power_state ? '0 4px 20px rgba(76, 175, 80, 0.3)' : undefined
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getDeviceIcon(device.device_type)}
              <Typography variant="h6" component="h2" noWrap>
                {device.device_name}
              </Typography>
            </Box>
            <Chip
              label={device.is_online ? 'Online' : 'Offline'}
              color={device.is_online ? 'success' : 'error'}
              size="small"
            />
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {device.device_type} • {device.device_id}
          </Typography>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="body2">
              IP: {device.ip_address}
            </Typography>
            <Typography variant="body2">
              MAC: {device.mac_address.slice(-8)}
            </Typography>
          </Box>

          {/* Device-specific information */}
          {device.device_type === 'Temperature Sensor' && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="error.main">
                🌡️ {device.temperature.toFixed(1)}°C
              </Typography>
              <Typography variant="body2" color="info.main">
                💧 {device.humidity.toFixed(1)}%
              </Typography>
            </Box>
          )}

          {device.device_type === 'Motion Sensor' && (
            <Box sx={{ mb: 2 }}>
              <Chip
                label={device.motion_detected ? '🔴 Motion Detected' : '🟢 No Motion'}
                color={device.motion_detected ? 'error' : 'success'}
                size="small"
              />
            </Box>
          )}

          {device.device_type === 'Door Sensor' && (
            <Box sx={{ mb: 2 }}>
              <Chip
                label={device.door_open ? '🔓 Door Open' : '🔒 Door Closed'}
                color={device.door_open ? 'warning' : 'success'}
                size="small"
              />
            </Box>
          )}

          {(device.device_type === 'Smart Light' || device.device_type === 'Smart Switch') && (
            <Box sx={{ mb: 2 }}>
              <Chip
                label={device.power_state ? '💡 ON' : '💡 OFF'}
                color={device.power_state ? 'success' : 'default'}
                size="small"
              />
              {device.supports_dimming && device.power_state && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption">Brightness: {device.brightness}%</Typography>
                  <Slider
                    value={device.brightness}
                    onChange={(e, value) => setBrightness(device.device_id, value)}
                    min={0}
                    max={100}
                    size="small"
                    sx={{ mt: 0.5 }}
                  />
                </Box>
              )}
            </Box>
          )}

          {/* Status indicators */}
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <Tooltip title={`Battery: ${device.battery_level}%`}>
              <Chip
                icon={<Battery3Bar />}
                label={`${device.battery_level}%`}
                size="small"
                color={device.battery_level > 20 ? 'success' : 'error'}
              />
            </Tooltip>
            <Tooltip title={`Signal: ${device.signal_strength} dBm`}>
              <Chip
                icon={device.signal_strength > -60 ? <SignalWifi4Bar /> : <WifiOff />}
                label={`${device.signal_strength}dBm`}
                size="small"
                color={device.signal_strength > -60 ? 'success' : 'warning'}
              />
            </Tooltip>
          </Box>
        </CardContent>

        <CardActions>
          {(device.device_type === 'Smart Light' || device.device_type === 'Smart Switch') && (
            <Button
              onClick={() => togglePower(device.device_id, device.power_state)}
              variant={device.power_state ? 'contained' : 'outlined'}
              color={device.power_state ? 'error' : 'success'}
              startIcon={device.power_state ? <PowerOff /> : <Power />}
              size="small"
            >
              {device.power_state ? 'Turn Off' : 'Turn On'}
            </Button>
          )}

          {device.device_type.includes('Sensor') && (
            <Button
              onClick={() => simulateSensor(device.device_id)}
              variant="outlined"
              startIcon={<Speed />}
              size="small"
            >
              Simulate
            </Button>
          )}

          <Button
            onClick={() => {
              setSelectedDevice(device);
              setDetailsOpen(true);
            }}
            variant="outlined"
            startIcon={<Visibility />}
            size="small"
          >
            Details
          </Button>
        </CardActions>
      </Card>
    </Grid>
  );

  const renderDeviceDetails = () => {
    if (!selectedDevice) return null;

    const chartData = sensorData[selectedDevice.device_id];

    return (
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {getDeviceIcon(selectedDevice.device_type)} {selectedDevice.device_name}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Device Information</Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell><strong>Device ID</strong></TableCell>
                      <TableCell>{selectedDevice.device_id}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Type</strong></TableCell>
                      <TableCell>{selectedDevice.device_type}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>IP Address</strong></TableCell>
                      <TableCell>{selectedDevice.ip_address}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>MAC Address</strong></TableCell>
                      <TableCell>{selectedDevice.mac_address}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Firmware</strong></TableCell>
                      <TableCell>{selectedDevice.firmware_version}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Last Seen</strong></TableCell>
                      <TableCell>{new Date(selectedDevice.last_seen).toLocaleString()}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            {selectedDevice.device_type === 'Temperature Sensor' && chartData && (
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Sensor Readings</Typography>
                <Box sx={{ height: 300 }}>
                  <Line
                    data={{
                      labels: chartData.labels,
                      datasets: [
                        {
                          label: 'Temperature (°C)',
                          data: chartData.temperature,
                          borderColor: 'rgb(255, 99, 132)',
                          backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        },
                        {
                          label: 'Humidity (%)',
                          data: chartData.humidity,
                          borderColor: 'rgb(54, 162, 235)',
                          backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: false
                        }
                      }
                    }}
                  />
                </Box>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          ESP32 Emulated Devices
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          <Button
            variant="outlined"
            onClick={fetchDevices}
            startIcon={<Refresh />}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Interactive Device Control:</strong> Control your emulated ESP32 devices directly from this dashboard. 
        Changes will be reflected in real-time on both the emulator dashboard and this interface.
      </Alert>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Chip
          label={`Total Devices: ${devices.length}`}
          color="primary"
          icon={<Settings />}
        />
        <Chip
          label={`Online: ${devices.filter(d => d.is_online).length}`}
          color="success"
          icon={<Wifi />}
        />
        <Chip
          label={`Powered On: ${devices.filter(d => d.power_state).length}`}
          color="warning"
          icon={<Power />}
        />
      </Box>

      <Grid container spacing={3}>
        {devices.map(renderDeviceCard)}
      </Grid>

      {devices.length === 0 && !loading && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          No emulated devices found. Make sure the ESP32 emulator is running on http://localhost:8090
          <br />
          <Button 
            variant="outlined" 
            size="small" 
            sx={{ mt: 1 }}
            onClick={() => window.open('http://localhost:8090', '_blank')}
          >
            Open Emulator Dashboard
          </Button>
        </Alert>
      )}

      {renderDeviceDetails()}

      {/* Floating action button to open emulator dashboard */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => window.open('http://localhost:8090', '_blank')}
      >
        <Badge badgeContent={devices.filter(d => d.is_online).length} color="success">
          <Settings />
        </Badge>
      </Fab>
    </Container>
  );
};

export default EmulatedDeviceControl;