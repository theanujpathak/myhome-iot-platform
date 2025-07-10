import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Lightbulb,
  Thermostat,
  Security,
  Power,
  Devices,
  Close,
  ExpandMore,
  CheckCircle
} from '@mui/icons-material';
import { useDevices } from '../contexts/DeviceContext';
import { toast } from 'react-toastify';

const InstantAddDevice = ({ open, onClose }) => {
  const { deviceTypes, locations, createDevice } = useDevices();
  const [selectedType, setSelectedType] = useState(null);
  const [deviceName, setDeviceName] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [advancedFields, setAdvancedFields] = useState({
    description: '',
    mac_address: '',
    ip_address: ''
  });

  const getDeviceIcon = (typeName) => {
    switch (typeName) {
      case 'Smart Light':
        return <Lightbulb sx={{ fontSize: 48, color: '#FFA726' }} />;
      case 'Temperature Sensor':
        return <Thermostat sx={{ fontSize: 48, color: '#42A5F5' }} />;
      case 'Door Sensor':
      case 'Motion Sensor':
        return <Security sx={{ fontSize: 48, color: '#EF5350' }} />;
      case 'Smart Switch':
      case 'Smart Plug':
        return <Power sx={{ fontSize: 48, color: '#66BB6A' }} />;
      default:
        return <Devices sx={{ fontSize: 48, color: '#BDBDBD' }} />;
    }
  };

  const getDefaultName = (type, location) => {
    if (!type || !location) return '';
    const locationName = locations.find(l => l.id === location)?.name || 'Room';
    return `${locationName} ${type.name}`;
  };

  const handleTypeSelect = (type) => {
    setSelectedType(type);
    if (selectedLocation) {
      setDeviceName(getDefaultName(type, selectedLocation));
    }
  };

  const handleLocationSelect = (locationId) => {
    setSelectedLocation(locationId);
    if (selectedType) {
      setDeviceName(getDefaultName(selectedType, locationId));
    }
  };

  const handleQuickAdd = async () => {
    if (!selectedType || !selectedLocation || !deviceName.trim()) {
      toast.error('Please select device type, location, and enter a name');
      return;
    }

    try {
      const deviceData = {
        name: deviceName.trim(),
        device_id: `${deviceName.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`,
        device_type_id: selectedType.id,
        location_id: selectedLocation,
        ...advancedFields
      };

      // Remove empty fields
      Object.keys(deviceData).forEach(key => {
        if (!deviceData[key]) delete deviceData[key];
      });

      await createDevice(deviceData);
      toast.success('Device added successfully!');
      
      // Reset form
      setSelectedType(null);
      setDeviceName('');
      setSelectedLocation('');
      setAdvancedFields({ description: '', mac_address: '', ip_address: '' });
      setShowAdvanced(false);
      onClose();
    } catch (error) {
      console.error('Failed to add device:', error);
      toast.error('Failed to add device');
    }
  };

  const handleClose = () => {
    setSelectedType(null);
    setDeviceName('');
    setSelectedLocation('');
    setAdvancedFields({ description: '', mac_address: '', ip_address: '' });
    setShowAdvanced(false);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Add New Device
          <IconButton onClick={handleClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {/* Step 1: Select Device Type */}
        <Typography variant="h6" gutterBottom>
          1. Choose Device Type
        </Typography>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {deviceTypes.slice(0, 6).map((type) => (
            <Grid item xs={6} sm={4} md={3} key={type.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  textAlign: 'center',
                  height: '120px',
                  border: selectedType?.id === type.id ? '2px solid' : '1px solid',
                  borderColor: selectedType?.id === type.id ? 'primary.main' : 'divider',
                  '&:hover': { borderColor: 'primary.main' }
                }}
                onClick={() => handleTypeSelect(type)}
              >
                <CardContent sx={{ pt: 2 }}>
                  {getDeviceIcon(type.name)}
                  <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
                    {type.name}
                  </Typography>
                  {selectedType?.id === type.id && (
                    <CheckCircle color="primary" sx={{ position: 'absolute', top: 4, right: 4 }} />
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Step 2: Select Location */}
        <Typography variant="h6" gutterBottom>
          2. Choose Location
        </Typography>
        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Select Location</InputLabel>
          <Select
            value={selectedLocation}
            onChange={(e) => handleLocationSelect(e.target.value)}
            label="Select Location"
          >
            {locations.map((location) => (
              <MenuItem key={location.id} value={location.id}>
                {location.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Step 3: Device Name */}
        <Typography variant="h6" gutterBottom>
          3. Device Name
        </Typography>
        <TextField
          fullWidth
          label="Device Name"
          value={deviceName}
          onChange={(e) => setDeviceName(e.target.value)}
          placeholder="e.g., Living Room Light"
          sx={{ mb: 3 }}
        />

        {/* Preview */}
        {selectedType && selectedLocation && deviceName && (
          <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px dashed' }}>
            <Typography variant="subtitle2" gutterBottom>
              Device Preview:
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {getDeviceIcon(selectedType.name)}
              <Box>
                <Typography variant="h6">{deviceName}</Typography>
                <Chip label={selectedType.name} size="small" sx={{ mr: 1 }} />
                <Chip 
                  label={locations.find(l => l.id === selectedLocation)?.name} 
                  size="small" 
                  variant="outlined" 
                />
              </Box>
            </Box>
          </Box>
        )}

        {/* Advanced Options */}
        <Accordion expanded={showAdvanced} onChange={() => setShowAdvanced(!showAdvanced)}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography>Advanced Options (Optional)</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  multiline
                  rows={2}
                  value={advancedFields.description}
                  onChange={(e) => setAdvancedFields({...advancedFields, description: e.target.value})}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="MAC Address"
                  value={advancedFields.mac_address}
                  onChange={(e) => setAdvancedFields({...advancedFields, mac_address: e.target.value})}
                  placeholder="00:1A:2B:3C:4D:5E"
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="IP Address"
                  value={advancedFields.ip_address}
                  onChange={(e) => setAdvancedFields({...advancedFields, ip_address: e.target.value})}
                  placeholder="192.168.1.100"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button
          onClick={handleQuickAdd}
          variant="contained"
          disabled={!selectedType || !selectedLocation || !deviceName.trim()}
          size="large"
        >
          Add Device
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default InstantAddDevice;