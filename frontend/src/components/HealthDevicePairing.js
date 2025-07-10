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
  Typography,
  Box,
  Card,
  CardContent,
  CardActionArea,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  LinearProgress
} from '@mui/material';
import {
  DirectionsRun,
  FavoriteOutlined,
  MonitorWeight,
  Bloodtype,
  Bedtime,
  Air,
  LocalHospital,
  Smartphone,
  Watch,
  Bluetooth,
  Wifi,
  CheckCircle,
  Error,
  Refresh,
  Settings
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useDevices } from '../contexts/DeviceContext';
import { useAuth } from '../contexts/AuthContext';

const HealthDevicePairing = ({ open, onClose, onDeviceAdded }) => {
  const { locations, createDevice, createDeviceType } = useDevices();
  const { user } = useAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [scanningDevices, setScanningDevices] = useState(false);
  const [selectedDeviceType, setSelectedDeviceType] = useState(null);
  const [detectedDevices, setDetectedDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [deviceConfig, setDeviceConfig] = useState({
    name: '',
    location_id: '',
    user_profile: {
      age: '',
      gender: '',
      height: '',
      weight: '',
      activity_level: 'moderate'
    },
    sync_settings: {
      auto_sync: true,
      sync_frequency: 'hourly',
      data_retention: '1_year'
    }
  });

  const steps = [
    'Select Device Type',
    'Scan for Devices', 
    'Configure Device',
    'User Profile',
    'Complete Setup'
  ];

  const healthDeviceTypes = [
    {
      id: 'fitness_tracker',
      name: 'Fitness Tracker',
      icon: <DirectionsRun />,
      description: 'Smartwatch, fitness band, or activity tracker',
      capabilities: ['heart_rate', 'step_counting', 'calorie_tracking', 'sleep_tracking'],
      brands: ['Apple Watch', 'Fitbit', 'Garmin', 'Samsung Galaxy Watch', 'Amazfit'],
      connection_type: 'bluetooth'
    },
    {
      id: 'smart_scale',
      name: 'Smart Scale',
      icon: <MonitorWeight />,
      description: 'Digital scale with body composition analysis',
      capabilities: ['weight_measurement', 'body_fat', 'muscle_mass', 'bone_density'],
      brands: ['Withings', 'Fitbit Aria', 'Eufy', 'Renpho', 'Tanita'],
      connection_type: 'wifi'
    },
    {
      id: 'blood_pressure_monitor',
      name: 'Blood Pressure Monitor',
      icon: <Bloodtype />,
      description: 'Digital blood pressure and heart rate monitor',
      capabilities: ['blood_pressure', 'heart_rate', 'pulse_pressure'],
      brands: ['Omron', 'Withings', 'QardioArm', 'iHealth', 'A&D Medical'],
      connection_type: 'bluetooth'
    },
    {
      id: 'sleep_tracker',
      name: 'Sleep Tracker',
      icon: <Bedtime />,
      description: 'Sleep monitoring device or mattress sensor',
      capabilities: ['sleep_tracking', 'sleep_stages', 'heart_rate_variability'],
      brands: ['Oura Ring', 'Sleep Number', 'Eight Sleep', 'Withings Sleep', 'ResMed'],
      connection_type: 'wifi'
    },
    {
      id: 'air_quality_monitor',
      name: 'Air Quality Monitor',
      icon: <Air />,
      description: 'Indoor air quality and environmental sensor',
      capabilities: ['air_quality', 'temperature', 'humidity', 'voc_levels'],
      brands: ['Dyson', 'PurpleAir', 'IQAir', 'Airthings', 'Awair'],
      connection_type: 'wifi'
    },
    {
      id: 'health_monitor',
      name: 'Health Monitor',
      icon: <FavoriteOutlined />,
      description: 'Multi-function health monitoring device',
      capabilities: ['heart_rate', 'oxygen_saturation', 'body_temperature'],
      brands: ['Masimo', 'Nonin', 'Beurer', 'iHealth', 'CheckMe'],
      connection_type: 'bluetooth'
    }
  ];

  const mockDetectedDevices = [
    {
      id: 'device_001',
      name: 'Apple Watch Series 9',
      brand: 'Apple',
      model: 'Series 9',
      signal_strength: 85,
      battery_level: 78,
      connection_type: 'bluetooth',
      mac_address: 'AA:BB:CC:DD:EE:01',
      capabilities: ['heart_rate', 'step_counting', 'calorie_tracking', 'sleep_tracking']
    },
    {
      id: 'device_002', 
      name: 'Fitbit Charge 5',
      brand: 'Fitbit',
      model: 'Charge 5',
      signal_strength: 92,
      battery_level: 65,
      connection_type: 'bluetooth',
      mac_address: 'AA:BB:CC:DD:EE:02',
      capabilities: ['heart_rate', 'step_counting', 'stress_monitoring', 'sleep_tracking']
    },
    {
      id: 'device_003',
      name: 'Withings Body+',
      brand: 'Withings',
      model: 'Body+',
      signal_strength: 78,
      battery_level: null,
      connection_type: 'wifi',
      mac_address: 'AA:BB:CC:DD:EE:03',
      capabilities: ['weight_measurement', 'body_fat', 'muscle_mass']
    }
  ];

  useEffect(() => {
    if (activeStep === 1 && selectedDeviceType) {
      handleDeviceScan();
    }
  }, [activeStep, selectedDeviceType]);

  const handleDeviceScan = async () => {
    setScanningDevices(true);
    
    // Simulate device scanning
    setTimeout(() => {
      const relevantDevices = mockDetectedDevices.filter(device => 
        selectedDeviceType.connection_type === device.connection_type &&
        device.capabilities.some(cap => selectedDeviceType.capabilities.includes(cap))
      );
      setDetectedDevices(relevantDevices);
      setScanningDevices(false);
    }, 3000);
  };

  const handleDeviceTypeSelect = (deviceType) => {
    setSelectedDeviceType(deviceType);
    setDeviceConfig(prev => ({
      ...prev,
      name: `${user?.first_name || 'User'}'s ${deviceType.name}`
    }));
    setActiveStep(1);
  };

  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
    setDeviceConfig(prev => ({
      ...prev,
      name: `${user?.first_name || 'User'}'s ${device.name}`
    }));
    setActiveStep(2);
  };

  const handleNext = () => {
    if (activeStep === 2 && (!deviceConfig.name || !deviceConfig.location_id)) {
      toast.error('Please fill in all required fields');
      return;
    }
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      // Create device type if it doesn't exist
      const deviceTypeData = {
        name: selectedDeviceType.name,
        description: selectedDeviceType.description,
        icon: selectedDeviceType.icon || 'monitor_heart',
        capabilities: selectedDeviceType.capabilities
      };

      // Create device type and get ID
      const createdDeviceType = await createDeviceType(deviceTypeData);
      
      // Create device
      const deviceData = {
        name: deviceConfig.name,
        description: `${selectedDevice.brand} ${selectedDevice.model} health device`,
        device_id: `HEALTH_${selectedDevice.mac_address.replace(/:/g, '')}`,
        location_id: deviceConfig.location_id,
        mac_address: selectedDevice.mac_address,
        device_type_id: createdDeviceType.id,
        configuration: {
          health_config: {
            user_profile: deviceConfig.user_profile,
            sync_settings: deviceConfig.sync_settings,
            capabilities: selectedDevice.capabilities
          }
        }
      };

      await createDevice(deviceData);
      toast.success(`${selectedDevice.name} paired successfully!`);
      
      if (onDeviceAdded) {
        onDeviceAdded(deviceData);
      }
      
      handleClose();
    } catch (error) {
      console.error('Failed to pair device:', error);
      toast.error('Failed to pair device. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setActiveStep(0);
    setSelectedDeviceType(null);
    setSelectedDevice(null);
    setDetectedDevices([]);
    setDeviceConfig({
      name: '',
      location_id: '',
      user_profile: {
        age: '',
        gender: '',
        height: '',
        weight: '',
        activity_level: 'moderate'
      },
      sync_settings: {
        auto_sync: true,
        sync_frequency: 'hourly',
        data_retention: '1_year'
      }
    });
    onClose();
  };

  const renderDeviceTypeSelection = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        What type of health device would you like to add?
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Select the category that best matches your device
      </Typography>
      
      <Grid container spacing={2}>
        {healthDeviceTypes.map((deviceType) => (
          <Grid item xs={12} sm={6} md={4} key={deviceType.id}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 4
                }
              }}
            >
              <CardActionArea onClick={() => handleDeviceTypeSelect(deviceType)}>
                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                  <Avatar
                    sx={{
                      bgcolor: 'primary.main',
                      width: 56,
                      height: 56,
                      mx: 'auto',
                      mb: 2
                    }}
                  >
                    {deviceType.icon}
                  </Avatar>
                  <Typography variant="h6" gutterBottom>
                    {deviceType.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {deviceType.description}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', justifyContent: 'center' }}>
                    {deviceType.capabilities.slice(0, 3).map((capability) => (
                      <Chip
                        key={capability}
                        label={capability.replace('_', ' ')}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderDeviceScanning = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Scanning for {selectedDeviceType?.name} devices...
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Make sure your device is in pairing mode and close to your phone/computer
      </Typography>

      {scanningDevices ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <CircularProgress size={60} sx={{ mb: 2 }} />
          <Typography variant="body1">
            Scanning for devices...
          </Typography>
          <LinearProgress sx={{ mt: 2, maxWidth: 400, mx: 'auto' }} />
        </Box>
      ) : (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1">
              Found {detectedDevices.length} device(s)
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={handleDeviceScan}
              variant="outlined"
              size="small"
            >
              Scan Again
            </Button>
          </Box>

          <List>
            {detectedDevices.map((device) => (
              <ListItem
                key={device.id}
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                  bgcolor: selectedDevice?.id === device.id ? 'action.selected' : 'transparent'
                }}
              >
                <ListItemAvatar>
                  <Avatar>
                    {device.connection_type === 'bluetooth' ? <Bluetooth /> : <Wifi />}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={device.name}
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        {device.brand} {device.model}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                        <Chip 
                          label={`Signal: ${device.signal_strength}%`} 
                          size="small" 
                          color={device.signal_strength > 80 ? 'success' : device.signal_strength > 50 ? 'warning' : 'error'}
                        />
                        {device.battery_level && (
                          <Chip 
                            label={`Battery: ${device.battery_level}%`} 
                            size="small" 
                            color={device.battery_level > 50 ? 'success' : 'warning'}
                          />
                        )}
                      </Box>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <Button
                    variant={selectedDevice?.id === device.id ? "contained" : "outlined"}
                    onClick={() => handleDeviceSelect(device)}
                    startIcon={selectedDevice?.id === device.id ? <CheckCircle /> : null}
                  >
                    {selectedDevice?.id === device.id ? 'Selected' : 'Select'}
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>

          {detectedDevices.length === 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              No devices found. Make sure your device is powered on and in pairing mode.
            </Alert>
          )}
        </Box>
      )}
    </Box>
  );

  const renderDeviceConfiguration = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Configure {selectedDevice?.name}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Set up basic device settings and location
      </Typography>

      <TextField
        fullWidth
        label="Device Name"
        value={deviceConfig.name}
        onChange={(e) => setDeviceConfig(prev => ({ ...prev, name: e.target.value }))}
        sx={{ mb: 2 }}
        required
      />

      <FormControl fullWidth sx={{ mb: 2 }} required>
        <InputLabel>Location</InputLabel>
        <Select
          value={deviceConfig.location_id}
          onChange={(e) => setDeviceConfig(prev => ({ ...prev, location_id: e.target.value }))}
          label="Location"
        >
          {locations.map((location) => (
            <MenuItem key={location.id} value={location.id}>
              {location.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Typography variant="subtitle1" sx={{ mb: 1 }}>
        Sync Settings
      </Typography>
      
      <FormControl fullWidth sx={{ mb: 1 }}>
        <InputLabel>Sync Frequency</InputLabel>
        <Select
          value={deviceConfig.sync_settings.sync_frequency}
          onChange={(e) => setDeviceConfig(prev => ({
            ...prev,
            sync_settings: { ...prev.sync_settings, sync_frequency: e.target.value }
          }))}
          label="Sync Frequency"
        >
          <MenuItem value="realtime">Real-time</MenuItem>
          <MenuItem value="hourly">Every Hour</MenuItem>
          <MenuItem value="daily">Daily</MenuItem>
          <MenuItem value="manual">Manual Only</MenuItem>
        </Select>
      </FormControl>
    </Box>
  );

  const renderUserProfile = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Set up your health profile
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        This information helps provide more accurate health insights
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="Age"
            type="number"
            value={deviceConfig.user_profile.age}
            onChange={(e) => setDeviceConfig(prev => ({
              ...prev,
              user_profile: { ...prev.user_profile, age: e.target.value }
            }))}
          />
        </Grid>
        <Grid item xs={6}>
          <FormControl fullWidth>
            <InputLabel>Gender</InputLabel>
            <Select
              value={deviceConfig.user_profile.gender}
              onChange={(e) => setDeviceConfig(prev => ({
                ...prev,
                user_profile: { ...prev.user_profile, gender: e.target.value }
              }))}
              label="Gender"
            >
              <MenuItem value="male">Male</MenuItem>
              <MenuItem value="female">Female</MenuItem>
              <MenuItem value="other">Other</MenuItem>
              <MenuItem value="prefer_not_to_say">Prefer not to say</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="Height (cm)"
            type="number"
            value={deviceConfig.user_profile.height}
            onChange={(e) => setDeviceConfig(prev => ({
              ...prev,
              user_profile: { ...prev.user_profile, height: e.target.value }
            }))}
          />
        </Grid>
        <Grid item xs={6}>
          <TextField
            fullWidth
            label="Weight (kg)"
            type="number"
            value={deviceConfig.user_profile.weight}
            onChange={(e) => setDeviceConfig(prev => ({
              ...prev,
              user_profile: { ...prev.user_profile, weight: e.target.value }
            }))}
          />
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>Activity Level</InputLabel>
            <Select
              value={deviceConfig.user_profile.activity_level}
              onChange={(e) => setDeviceConfig(prev => ({
                ...prev,
                user_profile: { ...prev.user_profile, activity_level: e.target.value }
              }))}
              label="Activity Level"
            >
              <MenuItem value="sedentary">Sedentary (little to no exercise)</MenuItem>
              <MenuItem value="lightly_active">Lightly Active (light exercise 1-3 days/week)</MenuItem>
              <MenuItem value="moderate">Moderately Active (moderate exercise 3-5 days/week)</MenuItem>
              <MenuItem value="very_active">Very Active (hard exercise 6-7 days/week)</MenuItem>
              <MenuItem value="extremely_active">Extremely Active (very hard exercise, physical job)</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Box>
  );

  const renderComplete = () => (
    <Box sx={{ textAlign: 'center' }}>
      <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
      <Typography variant="h6" gutterBottom>
        Ready to pair your device!
      </Typography>
      <Typography variant="body1" sx={{ mb: 3 }}>
        {selectedDevice?.name} will be added to your home automation system
      </Typography>

      <Card variant="outlined" sx={{ maxWidth: 400, mx: 'auto', mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Device Summary
          </Typography>
          <Box sx={{ textAlign: 'left' }}>
            <Typography variant="body2">
              <strong>Name:</strong> {deviceConfig.name}
            </Typography>
            <Typography variant="body2">
              <strong>Type:</strong> {selectedDeviceType?.name}
            </Typography>
            <Typography variant="body2">
              <strong>Brand:</strong> {selectedDevice?.brand} {selectedDevice?.model}
            </Typography>
            <Typography variant="body2">
              <strong>Location:</strong> {locations.find(l => l.id === deviceConfig.location_id)?.name}
            </Typography>
            <Typography variant="body2">
              <strong>Sync:</strong> {deviceConfig.sync_settings.sync_frequency}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return renderDeviceTypeSelection();
      case 1:
        return renderDeviceScanning();
      case 2:
        return renderDeviceConfiguration();
      case 3:
        return renderUserProfile();
      case 4:
        return renderComplete();
      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '70vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FavoriteOutlined />
          Add Health Device
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {getStepContent(activeStep)}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>
          Cancel
        </Button>
        {activeStep > 0 && activeStep < 4 && (
          <Button onClick={handleBack}>
            Back
          </Button>
        )}
        {activeStep < 3 && selectedDevice && (
          <Button onClick={handleNext} variant="contained">
            Next
          </Button>
        )}
        {activeStep === 3 && (
          <Button onClick={handleNext} variant="contained">
            Complete Profile
          </Button>
        )}
        {activeStep === 4 && (
          <Button 
            onClick={handleComplete} 
            variant="contained"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {loading ? 'Pairing...' : 'Pair Device'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default HealthDevicePairing;