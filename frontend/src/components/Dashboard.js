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
  ListItemSecondaryAction,
  Switch,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  Fab
} from '@mui/material';
import {
  Devices,
  LocationOn,
  Power,
  PowerOff,
  Lightbulb,
  Thermostat,
  Security,
  Add,
  Edit,
  Delete,
  Refresh,
  Dashboard as DashboardIcon,
  DevicesOther,
  TrendingUp,
  FavoriteOutlined,
  DirectionsRun,
  MonitorWeight,
  Bloodtype,
  Bedtime,
  Air,
  LocalHospital
} from '@mui/icons-material';
import { useDevices } from '../contexts/DeviceContext';
import { useAuth } from '../contexts/AuthContext';
import EnhancedDeviceControl from './EnhancedDeviceControl';
import EnhancedDevicePairing from './EnhancedDevicePairing';
import HealthDevicePairing from './HealthDevicePairing';

const Dashboard = () => {
  const { user } = useAuth();
  const {
    devices,
    locations,
    deviceTypes,
    loading,
    fetchDevices,
    sendDeviceCommand,
    createLocation,
    updateLocation,
    deleteLocation
  } = useDevices();

  const [tabValue, setTabValue] = useState(0);
  const [locationDialogOpen, setLocationDialogOpen] = useState(false);
  const [devicePairingOpen, setDevicePairingOpen] = useState(false);
  const [healthPairingOpen, setHealthPairingOpen] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [locationForm, setLocationForm] = useState({ name: '', description: '' });

  const onlineDevices = devices.filter(device => device.is_online);
  const offlineDevices = devices.filter(device => !device.is_online);
  const devicesByType = deviceTypes.map(type => ({
    ...type,
    count: devices.filter(device => device.device_type_id === type.id).length
  }));

  const handleDeviceToggle = async (device) => {
    try {
      // Get current power state from device states
      const powerState = device.device_states?.find(state => state.state_key === 'power');
      const isOn = powerState ? powerState.state_value === 'true' : false;
      
      await sendDeviceCommand(device.id, 'set_power', { power: !isOn });
    } catch (error) {
      console.error('Failed to toggle device:', error);
    }
  };

  const handleLocationDialog = (location = null) => {
    setSelectedLocation(location);
    setLocationForm(location ? { name: location.name, description: location.description || '' } : { name: '', description: '' });
    setLocationDialogOpen(true);
  };

  const handleLocationSubmit = async () => {
    try {
      if (selectedLocation) {
        await updateLocation(selectedLocation.id, locationForm);
      } else {
        await createLocation(locationForm);
      }
      setLocationDialogOpen(false);
      setLocationForm({ name: '', description: '' });
      setSelectedLocation(null);
    } catch (error) {
      console.error('Failed to save location:', error);
    }
  };

  const handleLocationDelete = async (locationId) => {
    if (window.confirm('Are you sure you want to delete this location?')) {
      try {
        await deleteLocation(locationId);
      } catch (error) {
        console.error('Failed to delete location:', error);
      }
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDeviceAdded = () => {
    fetchDevices();
    setDevicePairingOpen(false);
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
      // Health Device Icons
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

  const renderOverviewTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Welcome back, {user?.first_name || user?.username}!
      </Typography>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Devices sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Total Devices</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {devices.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Power sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Online</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                {onlineDevices.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PowerOff sx={{ mr: 1, color: 'error.main' }} />
                <Typography variant="h6">Offline</Typography>
              </Box>
              <Typography variant="h4" color="error.main">
                {offlineDevices.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <LocationOn sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">Locations</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                {locations.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Device Types */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Device Types
              </Typography>
              <List dense>
                {devicesByType.map((type) => (
                  <ListItem key={type.id}>
                    <ListItemIcon>
                      {getDeviceIcon(type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={type.name}
                      secondary={`${type.count} devices`}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Locations */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Locations
                </Typography>
                <Button
                  size="small"
                  startIcon={<Add />}
                  onClick={() => handleLocationDialog()}
                >
                  Add
                </Button>
              </Box>
              <List dense>
                {locations.map((location) => (
                  <ListItem key={location.id}>
                    <ListItemIcon>
                      <LocationOn />
                    </ListItemIcon>
                    <ListItemText
                      primary={location.name}
                      secondary={`${devices.filter(d => d.location_id === location.id).length} devices`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        size="small"
                        onClick={() => handleLocationDialog(location)}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleLocationDelete(location.id)}
                      >
                        <Delete />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
                {locations.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="No locations"
                      secondary="Add a location to organize your devices"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Devices */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Devices
              </Typography>
              <List dense>
                {devices.slice(0, 5).map((device) => (
                  <ListItem key={device.id}>
                    <ListItemIcon>
                      {getDeviceIcon(device.device_type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={device.name}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={device.is_online ? 'Online' : 'Offline'}
                            color={device.is_online ? 'success' : 'error'}
                            size="small"
                          />
                          {device.device_type?.capabilities?.includes('switch') && (
                            <Chip
                              label={isDeviceOn(device) ? 'On' : 'Off'}
                              color={isDeviceOn(device) ? 'primary' : 'default'}
                              size="small"
                            />
                          )}
                        </Box>
                      }
                    />
                    {device.device_type?.capabilities?.includes('switch') && device.is_online && (
                      <ListItemSecondaryAction>
                        <Switch
                          checked={isDeviceOn(device)}
                          onChange={() => handleDeviceToggle(device)}
                          size="small"
                        />
                      </ListItemSecondaryAction>
                    )}
                  </ListItem>
                ))}
                {devices.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="No devices"
                      secondary="Add devices to get started"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  const renderDevicesTab = () => (
    <Box>
      <Grid container spacing={3}>
        {devices.map((device) => (
          <Grid item xs={12} sm={6} md={4} key={device.id}>
            <EnhancedDeviceControl 
              device={device} 
              onUpdate={fetchDevices}
            />
          </Grid>
        ))}
        {devices.length === 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <DevicesOther sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No devices found
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Add your first device to start controlling your smart home
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setDevicePairingOpen(true)}
                >
                  Add Device
                </Button>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Smart Home Dashboard
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchDevices}
            disabled={loading}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleLocationDialog()}
            sx={{ mr: 2 }}
          >
            Add Location
          </Button>
          <Button
            variant="contained"
            startIcon={<FavoriteOutlined />}
            onClick={() => setHealthPairingOpen(true)}
            color="secondary"
          >
            Add Health Device
          </Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab 
            label="Overview" 
            icon={<DashboardIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Device Control" 
            icon={<DevicesOther />} 
            iconPosition="start"
          />
          <Tab 
            label="Analytics" 
            icon={<TrendingUp />} 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {tabValue === 0 && renderOverviewTab()}
      {tabValue === 1 && renderDevicesTab()}
      {tabValue === 2 && (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <TrendingUp sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Analytics Coming Soon
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Device usage analytics and energy monitoring will be available here
          </Typography>
        </Box>
      )}

      {/* Floating Action Button for Adding Devices */}
      <Fab
        color="primary"
        aria-label="add device"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setDevicePairingOpen(true)}
      >
        <Add />
      </Fab>

      {/* Enhanced Device Pairing Dialog */}
      <EnhancedDevicePairing
        open={devicePairingOpen}
        onClose={() => setDevicePairingOpen(false)}
        onDeviceAdded={handleDeviceAdded}
      />

      {/* Health Device Pairing Dialog */}
      <HealthDevicePairing
        open={healthPairingOpen}
        onClose={() => setHealthPairingOpen(false)}
        onDeviceAdded={handleDeviceAdded}
      />

      {/* Location Dialog */}
      <Dialog
        open={locationDialogOpen}
        onClose={() => setLocationDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {selectedLocation ? 'Edit Location' : 'Add Location'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Location Name"
            fullWidth
            variant="outlined"
            value={locationForm.name}
            onChange={(e) => setLocationForm({ ...locationForm, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={locationForm.description}
            onChange={(e) => setLocationForm({ ...locationForm, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLocationDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleLocationSubmit}
            variant="contained"
            disabled={!locationForm.name.trim()}
          >
            {selectedLocation ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Dashboard;
