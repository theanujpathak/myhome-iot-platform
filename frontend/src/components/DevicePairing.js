import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  DevicesOther,
  QrCode,
  Link,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import axios from 'axios';

const DevicePairing = ({ open, onClose, onDevicePaired }) => {
  const [step, setStep] = useState(1);
  const [deviceId, setDeviceId] = useState('');
  const [deviceSecret, setDeviceSecret] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [locationId, setLocationId] = useState('');
  const [locations, setLocations] = useState([]);
  const [availableDevices, setAvailableDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (open) {
      fetchLocations();
      fetchAvailableDevices();
    }
  }, [open]);

  const fetchLocations = async () => {
    try {
      const response = await axios.get('http://localhost:3002/api/locations');
      setLocations(response.data);
    } catch (error) {
      console.error('Failed to fetch locations:', error);
    }
  };

  const fetchAvailableDevices = async () => {
    try {
      const response = await axios.get('http://localhost:3002/api/devices/available');
      setAvailableDevices(response.data);
    } catch (error) {
      console.error('Failed to fetch available devices:', error);
    }
  };

  const handleReset = () => {
    setStep(1);
    setDeviceId('');
    setDeviceSecret('');
    setDeviceName('');
    setLocationId('');
    setError('');
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  const handleManualPairing = () => {
    setStep(2);
  };

  const handleAvailableDeviceSelect = (device) => {
    setDeviceId(device.device_id);
    setDeviceName(device.device_name);
    setStep(2);
  };

  const handlePairDevice = async () => {
    if (!deviceId || !deviceSecret) {
      setError('Device ID and Secret are required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const pairRequest = {
        device_id: deviceId,
        device_secret: deviceSecret,
        device_name: deviceName || undefined,
        location_id: locationId || undefined
      };

      const response = await axios.post('http://localhost:3002/api/devices/pair', pairRequest);
      
      if (response.data.success) {
        toast.success('Device paired successfully!');
        onDevicePaired && onDevicePaired(response.data.device);
        handleClose();
      } else {
        setError(response.data.message || 'Failed to pair device');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to pair device';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Choose Pairing Method
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card 
            sx={{ 
              cursor: 'pointer', 
              '&:hover': { bgcolor: 'action.hover' },
              height: '100%'
            }}
            onClick={handleManualPairing}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <QrCode sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Manual Entry</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Enter the device ID and secret manually. This information is usually found on the device label or setup documentation.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DevicesOther sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Available Devices</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Select from pre-registered devices available for pairing.
              </Typography>
              
              {availableDevices.length === 0 ? (
                <Alert severity="info" sx={{ mt: 2 }}>
                  No available devices found. Contact your administrator to register new devices.
                </Alert>
              ) : (
                <Box sx={{ mt: 2 }}>
                  {availableDevices.slice(0, 3).map((device) => (
                    <Box 
                      key={device.device_id}
                      sx={{ 
                        p: 1, 
                        mb: 1, 
                        border: '1px solid', 
                        borderColor: 'divider',
                        borderRadius: 1,
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' }
                      }}
                      onClick={() => handleAvailableDeviceSelect(device)}
                    >
                      <Typography variant="body2" fontWeight="medium">
                        {device.device_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {device.device_id}
                      </Typography>
                    </Box>
                  ))}
                  {availableDevices.length > 3 && (
                    <Typography variant="caption" color="text.secondary">
                      +{availableDevices.length - 3} more available
                    </Typography>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  const renderStep2 = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Device Pairing Details
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Device ID"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
            placeholder="ESP32_XXXXXXXX"
            variant="outlined"
            disabled={loading}
            helperText="8-character device identifier"
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Device Secret"
            value={deviceSecret}
            onChange={(e) => setDeviceSecret(e.target.value)}
            placeholder="Device secret key"
            variant="outlined"
            disabled={loading}
            type="password"
            helperText="32-character secret key"
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Device Name (Optional)"
            value={deviceName}
            onChange={(e) => setDeviceName(e.target.value)}
            placeholder="My ESP32 Device"
            variant="outlined"
            disabled={loading}
            helperText="Custom name for your device"
          />
        </Grid>
        
        <Grid item xs={12}>
          <FormControl fullWidth disabled={loading}>
            <InputLabel>Location (Optional)</InputLabel>
            <Select
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              label="Location (Optional)"
            >
              <MenuItem value="">
                <em>No location</em>
              </MenuItem>
              {locations.map((location) => (
                <MenuItem key={location.id} value={location.id}>
                  {location.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 3 }}>
        <Alert severity="info" icon={<Info />}>
          <Typography variant="body2">
            <strong>Where to find Device ID and Secret:</strong>
            <br />
            • Check the device label or sticker
            <br />
            • Look in the device setup documentation
            <br />
            • Contact your administrator if you don't have this information
          </Typography>
        </Alert>
      </Box>
    </Box>
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: '500px' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Link sx={{ mr: 1 }} />
          Pair New Device
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {step === 1 && renderStep1()}
        {step === 2 && renderStep2()}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        
        {step === 2 && (
          <Button onClick={() => setStep(1)} disabled={loading}>
            Back
          </Button>
        )}
        
        {step === 2 && (
          <Button
            onClick={handlePairDevice}
            variant="contained"
            disabled={loading || !deviceId || !deviceSecret}
            startIcon={loading ? <CircularProgress size={20} /> : <CheckCircle />}
          >
            {loading ? 'Pairing...' : 'Pair Device'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default DevicePairing;