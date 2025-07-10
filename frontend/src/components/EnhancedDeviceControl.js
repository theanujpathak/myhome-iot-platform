import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Grid,
  Button,
  Slider,
  Chip,
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
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  Lightbulb,
  LightbulbOutlined,
  Thermostat,
  Security,
  PowerSettingsNew,
  Settings,
  TrendingUp,
  Refresh,
  Schedule,
  Sensors,
  Speed,
  Brightness7,
  Brightness4,
  ColorLens,
  Timer,
  NotificationsActive,
  DeviceThermostat,
  DirectionsRun,
  MeetingRoom,
  Lock,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer
} from 'recharts';
import { useDevices } from '../contexts/DeviceContext';
import { toast } from 'react-toastify';
import emulatorService from '../services/emulatorService';

const EnhancedDeviceControl = ({ device, onUpdate }) => {
  const { sendDeviceCommand } = useDevices();
  const [configOpen, setConfigOpen] = useState(false);
  const [sensorData, setSensorData] = useState([]);
  const [deviceConfig, setDeviceConfig] = useState({
    auto_brightness: false,
    motion_sensitivity: 50,
    temperature_threshold: 25,
    schedule_enabled: false,
    notifications: true,
    dimming_curve: 'linear',
    color_temperature: 3000,
    fade_time: 1000
  });
  const [realTimeData, setRealTimeData] = useState({
    temperature: 22.5,
    humidity: 45,
    motion_detected: false,
    door_open: false,
    light_level: 75,
    power_consumption: 12.5
  });

  // Connect to emulator service and real-time data updates
  useEffect(() => {
    // Initialize emulator connection
    emulatorService.connect();

    // Subscribe to sensor readings
    const unsubscribeSensor = emulatorService.subscribe('sensor_reading', (data) => {
      if (data.device_id === device.device_id) {
        setRealTimeData(prev => ({
          ...prev,
          temperature: data.temperature || prev.temperature,
          humidity: data.humidity || prev.humidity,
          motion_detected: data.motion_detected !== undefined ? data.motion_detected : prev.motion_detected,
          light_level: data.light_level || prev.light_level,
          power_consumption: data.power_consumption || prev.power_consumption
        }));

        // Update chart data
        setSensorData(prev => {
          const newData = {
            time: new Date().toLocaleTimeString(),
            temperature: data.temperature || 22,
            humidity: data.humidity || 45,
            power: data.power_consumption || 0
          };
          return [...prev.slice(-19), newData];
        });
      }
    });

    // Subscribe to device state changes
    const unsubscribeState = emulatorService.subscribe('device_state_changed', (data) => {
      if (data.device_id === device.device_id) {
        onUpdate(); // Refresh device data
      }
    });

    // Fallback interval for data simulation when emulator is not available
    const interval = setInterval(() => {
      if (!emulatorService.isConnected) {
        setRealTimeData(prev => ({
          ...prev,
          temperature: 20 + Math.random() * 10,
          humidity: 30 + Math.random() * 40,
          motion_detected: Math.random() > 0.8,
          light_level: 50 + Math.random() * 50,
          power_consumption: device.power_state ? 10 + Math.random() * 15 : 0
        }));

        setSensorData(prev => {
          const newData = {
            time: new Date().toLocaleTimeString(),
            temperature: 20 + Math.random() * 10,
            humidity: 30 + Math.random() * 40,
            power: device.power_state ? 10 + Math.random() * 15 : 0
          };
          return [...prev.slice(-19), newData];
        });
      }
    }, 5000);

    return () => {
      unsubscribeSensor();
      unsubscribeState();
      clearInterval(interval);
    };
  }, [device.device_id, device.power_state, onUpdate]);

  const getDeviceIcon = () => {
    switch (device.device_type?.name) {
      case 'Smart Light':
        return device.power_state ? <Lightbulb color="primary" /> : <LightbulbOutlined />;
      case 'Temperature Sensor':
        return <Thermostat color="info" />;
      case 'Motion Sensor':
        return <Security color={realTimeData.motion_detected ? "error" : "success"} />;
      case 'Door Sensor':
        return realTimeData.door_open ? <MeetingRoom color="warning" /> : <Lock color="success" />;
      default:
        return <PowerSettingsNew />;
    }
  };

  const handlePowerToggle = async () => {
    try {
      // Try emulator service first, fallback to regular device service
      if (emulatorService.isConnected) {
        await emulatorService.controlDevice(device.device_id, 'power_state', !device.power_state);
      } else {
        await sendDeviceCommand(device.id, 'set_power', { power: !device.power_state });
      }
      onUpdate();
      toast.success(`${device.name} ${device.power_state ? 'turned off' : 'turned on'}`);
    } catch (error) {
      toast.error('Failed to toggle device power');
    }
  };

  const handleBrightnessChange = async (event, newValue) => {
    if (device.supports_dimming) {
      try {
        if (emulatorService.isConnected) {
          await emulatorService.controlDevice(device.device_id, 'brightness', newValue);
        } else {
          await sendDeviceCommand(device.id, 'set_brightness', { brightness: newValue });
        }
        onUpdate();
      } catch (error) {
        toast.error('Failed to adjust brightness');
      }
    }
  };

  const handleSimulateSensor = async () => {
    try {
      await emulatorService.simulateSensorReading(device.device_id);
      toast.success('Sensor reading simulated');
    } catch (error) {
      toast.error('Failed to simulate sensor reading');
    }
  };

  const handleConfigSave = async () => {
    try {
      await sendDeviceCommand(device.id, 'set_config', deviceConfig);
      setConfigOpen(false);
      toast.success('Device configuration updated');
      onUpdate();
    } catch (error) {
      toast.error('Failed to update device configuration');
    }
  };

  const getStatusColor = () => {
    if (!device.is_online) return 'error';
    if (device.power_state) return 'success';
    return 'default';
  };

  const renderSensorReadings = () => {
    if (device.device_type?.name === 'Temperature Sensor') {
      return (
        <Box sx={{ mt: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <DeviceThermostat color="error" sx={{ fontSize: 32 }} />
                <Typography variant="h6">{realTimeData.temperature.toFixed(1)}°C</Typography>
                <Typography variant="caption">Temperature</Typography>
              </Paper>
            </Grid>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Speed color="info" sx={{ fontSize: 32 }} />
                <Typography variant="h6">{realTimeData.humidity.toFixed(1)}%</Typography>
                <Typography variant="caption">Humidity</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      );
    }

    if (device.device_type?.name === 'Motion Sensor') {
      return (
        <Box sx={{ mt: 2 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <DirectionsRun color={realTimeData.motion_detected ? "error" : "success"} sx={{ fontSize: 40 }} />
            <Typography variant="h6">
              {realTimeData.motion_detected ? 'Motion Detected' : 'No Motion'}
            </Typography>
            <Chip
              label={realTimeData.motion_detected ? 'Active' : 'Clear'}
              color={realTimeData.motion_detected ? 'error' : 'success'}
              size="small"
            />
          </Paper>
        </Box>
      );
    }

    if (device.device_type?.name === 'Smart Light') {
      return (
        <Box sx={{ mt: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Brightness7 color="warning" sx={{ fontSize: 32 }} />
                <Typography variant="h6">{realTimeData.light_level.toFixed(0)}%</Typography>
                <Typography variant="caption">Light Level</Typography>
              </Paper>
            </Grid>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Speed color="info" sx={{ fontSize: 32 }} />
                <Typography variant="h6">{realTimeData.power_consumption.toFixed(1)}W</Typography>
                <Typography variant="caption">Power Usage</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      );
    }

    return null;
  };

  const renderControls = () => {
    const controls = [];

    // Power control for lights and switches
    if (['Smart Light', 'Smart Switch'].includes(device.device_type?.name)) {
      controls.push(
        <Button
          key="power"
          variant={device.power_state ? "contained" : "outlined"}
          color={device.power_state ? "error" : "success"}
          startIcon={device.power_state ? <Lightbulb /> : <LightbulbOutlined />}
          onClick={handlePowerToggle}
          disabled={!device.is_online}
          fullWidth
          sx={{ mb: 1 }}
        >
          {device.power_state ? 'Turn Off' : 'Turn On'}
        </Button>
      );

      // Brightness control for dimmable lights
      if (device.supports_dimming && device.power_state) {
        controls.push(
          <Box key="brightness" sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Brightness: {device.brightness || 100}%
            </Typography>
            <Slider
              value={device.brightness || 100}
              onChange={handleBrightnessChange}
              min={0}
              max={100}
              valueLabelDisplay="auto"
              disabled={!device.is_online}
            />
          </Box>
        );
      }
    }

    // Sensor simulation button for sensor devices
    if (['Temperature Sensor', 'Motion Sensor', 'Door Sensor'].includes(device.device_type?.name)) {
      controls.push(
        <Button
          key="simulate"
          variant="outlined"
          startIcon={<Sensors />}
          onClick={handleSimulateSensor}
          disabled={!device.is_online}
          fullWidth
          sx={{ mt: 1 }}
        >
          Simulate Reading
        </Button>
      );
    }

    // Configuration button
    controls.push(
      <Button
        key="config"
        variant="outlined"
        startIcon={<Settings />}
        onClick={() => setConfigOpen(true)}
        disabled={!device.is_online}
        fullWidth
        sx={{ mt: 1 }}
      >
        Configure
      </Button>
    );

    return controls;
  };

  const renderSensorChart = () => {
    if (sensorData.length === 0 || !['Temperature Sensor', 'Smart Light'].includes(device.device_type?.name)) {
      return null;
    }

    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Live Data Trends
        </Typography>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={sensorData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <RechartsTooltip />
            {device.device_type?.name === 'Temperature Sensor' && (
              <>
                <Line type="monotone" dataKey="temperature" stroke="#ff6b6b" strokeWidth={2} name="Temperature (°C)" />
                <Line type="monotone" dataKey="humidity" stroke="#4ecdc4" strokeWidth={2} name="Humidity (%)" />
              </>
            )}
            {device.device_type?.name === 'Smart Light' && (
              <Line type="monotone" dataKey="power" stroke="#45b7d1" strokeWidth={2} name="Power (W)" />
            )}
          </LineChart>
        </ResponsiveContainer>
      </Box>
    );
  };

  return (
    <>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
          {/* Device Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {getDeviceIcon()}
              <Box sx={{ ml: 1 }}>
                <Typography variant="h6" noWrap>
                  {device.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {device.device_type?.name}
                </Typography>
              </Box>
            </Box>
            <Chip
              label={device.is_online ? 'Online' : 'Offline'}
              color={getStatusColor()}
              size="small"
            />
          </Box>

          {/* Device Info */}
          <Grid container spacing={1} sx={{ mb: 2 }}>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">Device ID</Typography>
              <Typography variant="body2" fontFamily="monospace">
                {device.device_id || 'N/A'}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">Location</Typography>
              <Typography variant="body2">
                {device.location?.name || 'No location'}
              </Typography>
            </Grid>
          </Grid>

          {/* Real-time Sensor Readings */}
          {device.is_online && renderSensorReadings()}

          {/* Live Data Chart */}
          {device.is_online && renderSensorChart()}
        </CardContent>

        <CardActions sx={{ flexDirection: 'column', alignItems: 'stretch', p: 2 }}>
          {renderControls()}
        </CardActions>
      </Card>

      {/* Configuration Dialog */}
      <Dialog open={configOpen} onClose={() => setConfigOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Configure {device.name}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            {/* Basic Configuration */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Basic Settings</Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={deviceConfig.notifications}
                    onChange={(e) => setDeviceConfig({ ...deviceConfig, notifications: e.target.checked })}
                  />
                }
                label="Enable Notifications"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={deviceConfig.schedule_enabled}
                    onChange={(e) => setDeviceConfig({ ...deviceConfig, schedule_enabled: e.target.checked })}
                  />
                }
                label="Enable Scheduling"
              />
            </Grid>

            {/* Device-Specific Configuration */}
            {device.device_type?.name === 'Smart Light' && (
              <>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Light Settings</Typography>
                  <Divider sx={{ mb: 2 }} />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={deviceConfig.auto_brightness}
                        onChange={(e) => setDeviceConfig({ ...deviceConfig, auto_brightness: e.target.checked })}
                      />
                    }
                    label="Auto Brightness"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Dimming Curve</InputLabel>
                    <Select
                      value={deviceConfig.dimming_curve}
                      onChange={(e) => setDeviceConfig({ ...deviceConfig, dimming_curve: e.target.value })}
                      label="Dimming Curve"
                    >
                      <MenuItem value="linear">Linear</MenuItem>
                      <MenuItem value="logarithmic">Logarithmic</MenuItem>
                      <MenuItem value="exponential">Exponential</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography gutterBottom>Color Temperature: {deviceConfig.color_temperature}K</Typography>
                  <Slider
                    value={deviceConfig.color_temperature}
                    onChange={(e, value) => setDeviceConfig({ ...deviceConfig, color_temperature: value })}
                    min={2700}
                    max={6500}
                    step={100}
                    valueLabelDisplay="auto"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography gutterBottom>Fade Time: {deviceConfig.fade_time}ms</Typography>
                  <Slider
                    value={deviceConfig.fade_time}
                    onChange={(e, value) => setDeviceConfig({ ...deviceConfig, fade_time: value })}
                    min={0}
                    max={5000}
                    step={100}
                    valueLabelDisplay="auto"
                  />
                </Grid>
              </>
            )}

            {device.device_type?.name === 'Motion Sensor' && (
              <>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Motion Sensor Settings</Typography>
                  <Divider sx={{ mb: 2 }} />
                </Grid>

                <Grid item xs={12}>
                  <Typography gutterBottom>Motion Sensitivity: {deviceConfig.motion_sensitivity}%</Typography>
                  <Slider
                    value={deviceConfig.motion_sensitivity}
                    onChange={(e, value) => setDeviceConfig({ ...deviceConfig, motion_sensitivity: value })}
                    min={0}
                    max={100}
                    valueLabelDisplay="auto"
                  />
                </Grid>
              </>
            )}

            {device.device_type?.name === 'Temperature Sensor' && (
              <>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Temperature Sensor Settings</Typography>
                  <Divider sx={{ mb: 2 }} />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Temperature Threshold (°C)"
                    type="number"
                    value={deviceConfig.temperature_threshold}
                    onChange={(e) => setDeviceConfig({ ...deviceConfig, temperature_threshold: Number(e.target.value) })}
                    inputProps={{ min: -50, max: 100 }}
                  />
                </Grid>
              </>
            )}

            {/* Advanced Configuration */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Advanced Settings</Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12}>
              <Alert severity="info">
                These settings will be applied to your device and stored in its memory. Some changes may require a device restart.
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigOpen(false)}>Cancel</Button>
          <Button onClick={handleConfigSave} variant="contained">
            Save Configuration
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default EnhancedDeviceControl;