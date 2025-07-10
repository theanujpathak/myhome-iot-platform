import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Box,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Switch,
  FormControlLabel,
  Slider,
  Alert,
  CircularProgress,
  Divider,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Wifi,
  DevicesOther,
  Settings,
  CheckCircle,
  Error,
  Refresh,
  QrCodeScanner,
  Router,
  Security,
  Lightbulb,
  Thermostat,
  DirectionsRun,
  PowerSettingsNew,
  Schedule,
  Notifications,
  ColorLens,
  Speed,
  Brightness7
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useDevices } from '../contexts/DeviceContext';

const EnhancedDevicePairing = ({ open, onClose, onDeviceAdded }) => {
  const { locations, deviceTypes, createDevice } = useDevices();
  const [activeStep, setActiveStep] = useState(0);
  const [availableDevices, setAvailableDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [deviceForm, setDeviceForm] = useState({
    name: '',
    location_id: '',
    device_type_id: '',
    description: '',
    device_id: '',
    mac_address: '',
    ip_address: ''
  });
  const [deviceConfig, setDeviceConfig] = useState({
    // WiFi Configuration
    wifi_ssid: '',
    wifi_password: '',
    wifi_security: 'WPA2',
    
    // Device Settings
    auto_discovery: true,
    heartbeat_interval: 30,
    update_interval: 5,
    
    // Smart Light Configuration
    default_brightness: 80,
    auto_brightness: false,
    color_temperature: 3000,
    fade_time: 1000,
    dimming_curve: 'linear',
    
    // Sensor Configuration
    motion_sensitivity: 70,
    temperature_threshold: 25,
    humidity_threshold: 60,
    reporting_interval: 10,
    
    // Schedule & Automation
    schedule_enabled: true,
    notifications_enabled: true,
    automation_enabled: true,
    
    // Security
    encryption_enabled: true,
    secure_connection: true,
    device_password: ''
  });

  const steps = [
    'Scan for Devices',
    'Select Device',
    'Configure WiFi',
    'Device Settings',
    'Final Setup'
  ];

  useEffect(() => {
    if (open) {
      handleScanDevices();
    }
  }, [open]);

  const handleScanDevices = async () => {
    setScanning(true);
    try {
      // Simulate scanning for available devices
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockDevices = [
        {
          id: 'ESP32_001',
          name: 'Smart Light - Living Room',
          type: 'Smart Light',
          mac: 'AA:BB:CC:DD:EE:01',
          ip: '192.168.1.100',
          signal_strength: -45,
          status: 'available'
        },
        {
          id: 'ESP32_002',
          name: 'Temperature Sensor - Kitchen',
          type: 'Temperature Sensor',
          mac: 'AA:BB:CC:DD:EE:02',
          ip: '192.168.1.101',
          signal_strength: -38,
          status: 'available'
        },
        {
          id: 'ESP32_003',
          name: 'Motion Sensor - Hallway',
          type: 'Motion Sensor',
          mac: 'AA:BB:CC:DD:EE:03',
          ip: '192.168.1.102',
          signal_strength: -52,
          status: 'available'
        }
      ];
      
      setAvailableDevices(mockDevices);
      toast.success(`Found ${mockDevices.length} available devices`);
    } catch (error) {
      toast.error('Failed to scan for devices');
    } finally {
      setScanning(false);
    }
  };

  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
    setDeviceForm({
      ...deviceForm,
      name: device.name,
      device_id: device.id,
      mac_address: device.mac,
      ip_address: device.ip,
      device_type_id: getDeviceTypeId(device.type)
    });
    setActiveStep(1);
  };

  const getDeviceTypeId = (typeName) => {
    const deviceType = deviceTypes.find(type => type.name === typeName);
    return deviceType ? deviceType.id : '';
  };

  const getSignalIcon = (strength) => {
    if (strength > -50) return <Wifi color="success" />;
    if (strength > -70) return <Wifi color="warning" />;
    return <Wifi color="error" />;
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleFinishSetup = async () => {
    try {
      // Create the device with full configuration
      const deviceData = {
        ...deviceForm,
        configuration: deviceConfig,
        is_configured: true
      };

      await createDevice(deviceData);
      
      toast.success('Device paired and configured successfully!');
      onDeviceAdded();
      handleClose();
    } catch (error) {
      toast.error('Failed to complete device setup');
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setSelectedDevice(null);
    setAvailableDevices([]);
    setDeviceForm({
      name: '',
      location_id: '',
      device_type_id: '',
      description: '',
      device_id: '',
      mac_address: '',
      ip_address: ''
    });
    setDeviceConfig({
      wifi_ssid: '',
      wifi_password: '',
      wifi_security: 'WPA2',
      auto_discovery: true,
      heartbeat_interval: 30,
      update_interval: 5,
      default_brightness: 80,
      auto_brightness: false,
      color_temperature: 3000,
      fade_time: 1000,
      dimming_curve: 'linear',
      motion_sensitivity: 70,
      temperature_threshold: 25,
      humidity_threshold: 60,
      reporting_interval: 10,
      schedule_enabled: true,
      notifications_enabled: true,
      automation_enabled: true,
      encryption_enabled: true,
      secure_connection: true,
      device_password: ''
    });
    onClose();
  };

  const renderScanStep = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Available Devices</Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleScanDevices}
          disabled={scanning}
        >
          {scanning ? 'Scanning...' : 'Scan Again'}
        </Button>
      </Box>

      {scanning && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Scanning for devices...</Typography>
        </Box>
      )}

      <Grid container spacing={2}>
        {availableDevices.map((device) => (
          <Grid item xs={12} key={device.id}>
            <Card 
              sx={{ cursor: 'pointer', '&:hover': { elevation: 4 } }}
              onClick={() => handleDeviceSelect(device)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <DevicesOther sx={{ mr: 2 }} />
                    <Box>
                      <Typography variant="h6">{device.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {device.type} • {device.id}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        MAC: {device.mac} • IP: {device.ip}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    {getSignalIcon(device.signal_strength)}
                    <Typography variant="caption" display="block">
                      {device.signal_strength} dBm
                    </Typography>
                    <Chip label={device.status} color="success" size="small" />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {availableDevices.length === 0 && !scanning && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No devices found. Make sure your devices are in pairing mode and click "Scan Again".
        </Alert>
      )}
    </Box>
  );

  const renderDeviceDetailsStep = () => (
    <Box>
      <Typography variant="h6" gutterBottom>Device Information</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Device Name"
            value={deviceForm.name}
            onChange={(e) => setDeviceForm({ ...deviceForm, name: e.target.value })}
            required
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <FormControl fullWidth required>
            <InputLabel>Location</InputLabel>
            <Select
              value={deviceForm.location_id}
              onChange={(e) => setDeviceForm({ ...deviceForm, location_id: e.target.value })}
              label="Location"
            >
              {locations.map((location) => (
                <MenuItem key={location.id} value={location.id}>
                  {location.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Description"
            value={deviceForm.description}
            onChange={(e) => setDeviceForm({ ...deviceForm, description: e.target.value })}
            multiline
            rows={2}
          />
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" gutterBottom>Device Details</Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body2">Device ID: {selectedDevice?.id}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2">Type: {selectedDevice?.type}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2">MAC: {selectedDevice?.mac}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2">IP: {selectedDevice?.ip}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );

  const renderWiFiConfigStep = () => (
    <Box>
      <Typography variant="h6" gutterBottom>WiFi Configuration</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} sm={8}>
          <TextField
            fullWidth
            label="WiFi Network (SSID)"
            value={deviceConfig.wifi_ssid}
            onChange={(e) => setDeviceConfig({ ...deviceConfig, wifi_ssid: e.target.value })}
            required
          />
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth>
            <InputLabel>Security</InputLabel>
            <Select
              value={deviceConfig.wifi_security}
              onChange={(e) => setDeviceConfig({ ...deviceConfig, wifi_security: e.target.value })}
              label="Security"
            >
              <MenuItem value="WPA2">WPA2</MenuItem>
              <MenuItem value="WPA3">WPA3</MenuItem>
              <MenuItem value="WEP">WEP</MenuItem>
              <MenuItem value="Open">Open</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="WiFi Password"
            type="password"
            value={deviceConfig.wifi_password}
            onChange={(e) => setDeviceConfig({ ...deviceConfig, wifi_password: e.target.value })}
            required={deviceConfig.wifi_security !== 'Open'}
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle2" gutterBottom>Connection Settings</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography gutterBottom>Heartbeat Interval: {deviceConfig.heartbeat_interval}s</Typography>
              <Slider
                value={deviceConfig.heartbeat_interval}
                onChange={(e, value) => setDeviceConfig({ ...deviceConfig, heartbeat_interval: value })}
                min={10}
                max={300}
                step={10}
                valueLabelDisplay="auto"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography gutterBottom>Update Interval: {deviceConfig.update_interval}s</Typography>
              <Slider
                value={deviceConfig.update_interval}
                onChange={(e, value) => setDeviceConfig({ ...deviceConfig, update_interval: value })}
                min={1}
                max={60}
                step={1}
                valueLabelDisplay="auto"
              />
            </Grid>
          </Grid>
        </Grid>

        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={deviceConfig.auto_discovery}
                onChange={(e) => setDeviceConfig({ ...deviceConfig, auto_discovery: e.target.checked })}
              />
            }
            label="Enable Auto Discovery"
          />
        </Grid>
      </Grid>
    </Box>
  );

  const renderDeviceSettingsStep = () => (
    <Box>
      <Typography variant="h6" gutterBottom>Device-Specific Settings</Typography>
      
      {selectedDevice?.type === 'Smart Light' && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>Light Configuration</Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography gutterBottom>Default Brightness: {deviceConfig.default_brightness}%</Typography>
            <Slider
              value={deviceConfig.default_brightness}
              onChange={(e, value) => setDeviceConfig({ ...deviceConfig, default_brightness: value })}
              min={1}
              max={100}
              valueLabelDisplay="auto"
            />
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

          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={deviceConfig.auto_brightness}
                  onChange={(e) => setDeviceConfig({ ...deviceConfig, auto_brightness: e.target.checked })}
                />
              }
              label="Enable Auto Brightness"
            />
          </Grid>
        </Grid>
      )}

      {selectedDevice?.type === 'Temperature Sensor' && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>Sensor Configuration</Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Temperature Threshold (°C)"
              type="number"
              value={deviceConfig.temperature_threshold}
              onChange={(e) => setDeviceConfig({ ...deviceConfig, temperature_threshold: Number(e.target.value) })}
            />
          </Grid>

          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Humidity Threshold (%)"
              type="number"
              value={deviceConfig.humidity_threshold}
              onChange={(e) => setDeviceConfig({ ...deviceConfig, humidity_threshold: Number(e.target.value) })}
            />
          </Grid>

          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Reporting Interval (s)"
              type="number"
              value={deviceConfig.reporting_interval}
              onChange={(e) => setDeviceConfig({ ...deviceConfig, reporting_interval: Number(e.target.value) })}
            />
          </Grid>
        </Grid>
      )}

      {selectedDevice?.type === 'Motion Sensor' && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="subtitle2" gutterBottom>Motion Sensor Configuration</Typography>
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

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Reporting Interval (s)"
              type="number"
              value={deviceConfig.reporting_interval}
              onChange={(e) => setDeviceConfig({ ...deviceConfig, reporting_interval: Number(e.target.value) })}
            />
          </Grid>
        </Grid>
      )}

      {/* Common Settings */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Typography variant="subtitle2" gutterBottom>General Settings</Typography>
          <Divider sx={{ mb: 2 }} />
        </Grid>

        <Grid item xs={12} sm={4}>
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

        <Grid item xs={12} sm={4}>
          <FormControlLabel
            control={
              <Switch
                checked={deviceConfig.notifications_enabled}
                onChange={(e) => setDeviceConfig({ ...deviceConfig, notifications_enabled: e.target.checked })}
              />
            }
            label="Enable Notifications"
          />
        </Grid>

        <Grid item xs={12} sm={4}>
          <FormControlLabel
            control={
              <Switch
                checked={deviceConfig.automation_enabled}
                onChange={(e) => setDeviceConfig({ ...deviceConfig, automation_enabled: e.target.checked })}
              />
            }
            label="Enable Automation"
          />
        </Grid>
      </Grid>
    </Box>
  );

  const renderFinalSetupStep = () => (
    <Box>
      <Typography variant="h6" gutterBottom>Setup Summary</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>Device Information</Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Name" secondary={deviceForm.name} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Type" secondary={selectedDevice?.type} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Location" secondary={locations.find(l => l.id == deviceForm.location_id)?.name} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Device ID" secondary={selectedDevice?.id} />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>Configuration</Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="WiFi Network" secondary={deviceConfig.wifi_ssid} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Security" secondary={deviceConfig.wifi_security} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Auto Discovery" secondary={deviceConfig.auto_discovery ? 'Enabled' : 'Disabled'} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Scheduling" secondary={deviceConfig.schedule_enabled ? 'Enabled' : 'Disabled'} />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Alert severity="info">
            Your device will be configured with these settings. You can modify them later from the device management panel.
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return renderScanStep();
      case 1:
        return renderDeviceDetailsStep();
      case 2:
        return renderWiFiConfigStep();
      case 3:
        return renderDeviceSettingsStep();
      case 4:
        return renderFinalSetupStep();
      default:
        return 'Unknown step';
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Add New Device
      </DialogTitle>
      <DialogContent>
        <Box sx={{ width: '100%' }}>
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((label, index) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
                <StepContent>
                  <Box sx={{ mb: 2 }}>
                    {getStepContent(index)}
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Button
                      variant="contained"
                      onClick={index === steps.length - 1 ? handleFinishSetup : handleNext}
                      sx={{ mt: 1, mr: 1 }}
                      disabled={
                        (index === 0 && !selectedDevice) ||
                        (index === 1 && (!deviceForm.name || !deviceForm.location_id)) ||
                        (index === 2 && (!deviceConfig.wifi_ssid || (!deviceConfig.wifi_password && deviceConfig.wifi_security !== 'Open')))
                      }
                    >
                      {index === steps.length - 1 ? 'Finish Setup' : 'Continue'}
                    </Button>
                    <Button
                      disabled={index === 0}
                      onClick={handleBack}
                      sx={{ mt: 1, mr: 1 }}
                    >
                      Back
                    </Button>
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
};

export default EnhancedDevicePairing;