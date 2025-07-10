import React, { useState } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Button,
  IconButton,
  Switch,
  Slider,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Fab,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Power,
  PowerOff,
  Lightbulb,
  Thermostat,
  Security,
  Devices,
  LocationOn,
  Settings,
  Brightness6,
  Palette
} from '@mui/icons-material';
import { useDevices } from '../contexts/DeviceContext';
import { useAuth } from '../contexts/AuthContext';
import QuickDeviceSetup from './QuickDeviceSetup';
import InstantAddDevice from './InstantAddDevice';
import ESP32DeviceSetup from './ESP32DeviceSetup';
import DevicePairing from './DevicePairing';

const DeviceControl = () => {
  const { isAdmin } = useAuth();
  const {
    devices,
    locations,
    deviceTypes,
    loading,
    createDevice,
    updateDevice,
    deleteDevice,
    sendDeviceCommand
  } = useDevices();

  const [deviceDialogOpen, setDeviceDialogOpen] = useState(false);
  const [quickSetupOpen, setQuickSetupOpen] = useState(false);
  const [instantAddOpen, setInstantAddOpen] = useState(false);
  const [esp32SetupOpen, setEsp32SetupOpen] = useState(false);
  const [devicePairingOpen, setDevicePairingOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [deviceForm, setDeviceForm] = useState({
    name: '',
    description: '',
    device_id: '',
    device_type_id: '',
    location_id: '',
    mac_address: '',
    ip_address: ''
  });
  const [selectedLocation, setSelectedLocation] = useState('all');

  const filteredDevices = selectedLocation === 'all' 
    ? devices 
    : devices.filter(device => 
        selectedLocation === 'unassigned' 
          ? !device.location_id 
          : device.location_id === parseInt(selectedLocation)
      );

  const handleDeviceDialog = (device = null) => {
    setSelectedDevice(device);
    if (device) {
      setDeviceForm({
        name: device.name,
        description: device.description || '',
        device_id: device.device_id,
        device_type_id: device.device_type_id,
        location_id: device.location_id || '',
        mac_address: device.mac_address || '',
        ip_address: device.ip_address || ''
      });
    } else {
      setDeviceForm({
        name: '',
        description: '',
        device_id: '',
        device_type_id: '',
        location_id: '',
        mac_address: '',
        ip_address: ''
      });
    }
    setDeviceDialogOpen(true);
  };

  const handleDeviceSubmit = async () => {
    try {
      const formData = { ...deviceForm };
      if (!formData.location_id) delete formData.location_id;
      if (!formData.mac_address) delete formData.mac_address;
      if (!formData.ip_address) delete formData.ip_address;

      if (selectedDevice) {
        await updateDevice(selectedDevice.id, formData);
      } else {
        await createDevice(formData);
      }
      setDeviceDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Failed to save device:', error);
    }
  };

  const handleDeviceDelete = async (deviceId) => {
    if (window.confirm('Are you sure you want to delete this device?')) {
      try {
        await deleteDevice(deviceId);
      } catch (error) {
        console.error('Failed to delete device:', error);
      }
    }
  };

  const resetForm = () => {
    setDeviceForm({
      name: '',
      description: '',
      device_id: '',
      device_type_id: '',
      location_id: '',
      mac_address: '',
      ip_address: ''
    });
    setSelectedDevice(null);
  };

  const getDeviceIcon = (deviceType) => {
    switch (deviceType?.name) {
      case 'Smart Light':
        return <Lightbulb />;
      case 'Temperature Sensor':
        return <Thermostat />;
      case 'Door Sensor':
      case 'Motion Sensor':
        return <Security />;
      default:
        return <Devices />;
    }
  };

  const getDeviceStateValue = (device, stateKey) => {
    const state = device.device_states?.find(s => s.state_key === stateKey);
    return state ? state.state_value : null;
  };

  const isDeviceOn = (device) => {
    const powerState = getDeviceStateValue(device, 'power');
    return powerState === 'true';
  };

  const handleDeviceToggle = async (device) => {
    try {
      const isOn = isDeviceOn(device);
      await sendDeviceCommand(device.id, 'set_power', { power: !isOn });
    } catch (error) {
      console.error('Failed to toggle device:', error);
    }
  };

  const handleBrightnessChange = async (device, brightness) => {
    try {
      await sendDeviceCommand(device.id, 'set_brightness', { brightness });
    } catch (error) {
      console.error('Failed to set brightness:', error);
    }
  };

  const renderDeviceControls = (device) => {
    const capabilities = device.device_type?.capabilities || [];
    const brightness = getDeviceStateValue(device, 'brightness');
    const temperature = getDeviceStateValue(device, 'temperature');
    const humidity = getDeviceStateValue(device, 'humidity');

    return (
      <Box sx={{ mt: 2 }}>
        {capabilities.includes('switch') && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Power sx={{ mr: 1 }} />
            <Typography sx={{ flexGrow: 1 }}>Power</Typography>
            <Switch
              checked={isDeviceOn(device)}
              onChange={() => handleDeviceToggle(device)}
              disabled={!device.is_online}
            />
          </Box>
        )}

        {capabilities.includes('dimmer') && device.is_online && isDeviceOn(device) && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Brightness6 sx={{ mr: 1 }} />
              <Typography>Brightness: {brightness || 0}%</Typography>
            </Box>
            <Slider
              value={parseInt(brightness) || 0}
              onChange={(e, value) => handleBrightnessChange(device, value)}
              min={0}
              max={100}
              disabled={!device.is_online || !isDeviceOn(device)}
            />
          </Box>
        )}

        {capabilities.includes('temperature') && temperature && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Thermostat sx={{ mr: 1 }} />
            <Typography>Temperature: {temperature}°C</Typography>
          </Box>
        )}

        {capabilities.includes('humidity') && humidity && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Thermostat sx={{ mr: 1 }} />
            <Typography>Humidity: {humidity}%</Typography>
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Device Control
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Filter by Location</InputLabel>
            <Select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              label="Filter by Location"
            >
              <MenuItem value="all">All Locations</MenuItem>
              <MenuItem value="unassigned">Unassigned</MenuItem>
              {locations.map((location) => (
                <MenuItem key={location.id} value={location.id}>
                  {location.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setInstantAddOpen(true)}
            size="large"
          >
            Add Device
          </Button>
          <Button
            variant="outlined"
            onClick={() => setQuickSetupOpen(true)}
          >
            Quick Setup
          </Button>
          <Button
            variant="outlined"
            onClick={() => setEsp32SetupOpen(true)}
            startIcon={<Devices />}
          >
            ESP32 Setup
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => setDevicePairingOpen(true)}
            startIcon={<Devices />}
          >
            Pair Device
          </Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {devices.length === 0 && !loading && (
        <Alert severity="info" sx={{ mb: 3 }}>
          No devices found. Add your first device to get started!
        </Alert>
      )}

      <Grid container spacing={3}>
        {filteredDevices.map((device) => (
          <Grid item xs={12} sm={6} md={4} key={device.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {getDeviceIcon(device.device_type)}
                  <Box sx={{ ml: 2, flexGrow: 1 }}>
                    <Typography variant="h6" component="h2">
                      {device.name}
                    </Typography>
                    <Typography color="text.secondary" variant="body2">
                      {device.device_type?.name}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <IconButton
                      size="small"
                      onClick={() => handleDeviceDialog(device)}
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDeviceDelete(device.id)}
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Chip
                    label={device.is_online ? 'Online' : 'Offline'}
                    color={device.is_online ? 'success' : 'error'}
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  {device.location && (
                    <Chip
                      icon={<LocationOn />}
                      label={device.location.name}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>

                {device.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {device.description}
                  </Typography>
                )}

                {renderDeviceControls(device)}

                {device.last_seen && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                    Last seen: {new Date(device.last_seen).toLocaleString()}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Add Device FAB */}
      <Fab
        color="primary"
        aria-label="add device"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => handleDeviceDialog()}
      >
        <Add />
      </Fab>

      {/* Device Dialog */}
      <Dialog
        open={deviceDialogOpen}
        onClose={() => setDeviceDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {selectedDevice ? 'Edit Device' : 'Add Device'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Device Name"
            fullWidth
            variant="outlined"
            value={deviceForm.name}
            onChange={(e) => setDeviceForm({ ...deviceForm, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            label="Device ID"
            fullWidth
            variant="outlined"
            value={deviceForm.device_id}
            onChange={(e) => setDeviceForm({ ...deviceForm, device_id: e.target.value })}
            helperText="Unique identifier for this device"
            sx={{ mb: 2 }}
            disabled={!!selectedDevice}
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Device Type</InputLabel>
            <Select
              value={deviceForm.device_type_id}
              onChange={(e) => setDeviceForm({ ...deviceForm, device_type_id: e.target.value })}
              label="Device Type"
            >
              {deviceTypes.map((type) => (
                <MenuItem key={type.id} value={type.id}>
                  {type.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Location</InputLabel>
            <Select
              value={deviceForm.location_id}
              onChange={(e) => setDeviceForm({ ...deviceForm, location_id: e.target.value })}
              label="Location"
            >
              <MenuItem value="">No Location</MenuItem>
              {locations.map((location) => (
                <MenuItem key={location.id} value={location.id}>
                  {location.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={deviceForm.description}
            onChange={(e) => setDeviceForm({ ...deviceForm, description: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            margin="dense"
            label="MAC Address"
            fullWidth
            variant="outlined"
            value={deviceForm.mac_address}
            onChange={(e) => setDeviceForm({ ...deviceForm, mac_address: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            margin="dense"
            label="IP Address"
            fullWidth
            variant="outlined"
            value={deviceForm.ip_address}
            onChange={(e) => setDeviceForm({ ...deviceForm, ip_address: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeviceDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeviceSubmit}
            variant="contained"
            disabled={!deviceForm.name.trim() || !deviceForm.device_id.trim() || !deviceForm.device_type_id}
          >
            {selectedDevice ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Quick Device Setup */}
      <QuickDeviceSetup
        open={quickSetupOpen}
        onClose={() => setQuickSetupOpen(false)}
      />

      {/* Instant Add Device */}
      <InstantAddDevice
        open={instantAddOpen}
        onClose={() => setInstantAddOpen(false)}
      />

      {/* ESP32 Device Setup */}
      <ESP32DeviceSetup
        open={esp32SetupOpen}
        onClose={() => setEsp32SetupOpen(false)}
      />

      {/* Device Pairing */}
      <DevicePairing
        open={devicePairingOpen}
        onClose={() => setDevicePairingOpen(false)}
        onDevicePaired={() => {
          // Refresh devices list after pairing
          window.location.reload();
        }}
      />
    </Container>
  );
};

export default DeviceControl;