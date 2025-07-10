import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  LinearProgress,
  IconButton,
  Fab
} from '@mui/material';
import {
  Search,
  Wifi,
  CheckCircle,
  Error,
  Lightbulb,
  Thermostat,
  Security,
  Power,
  Devices,
  Add,
  Refresh,
  Close
} from '@mui/icons-material';
import { useDevices } from '../contexts/DeviceContext';
import { toast } from 'react-toastify';

const QuickDeviceSetup = ({ open, onClose }) => {
  const { deviceTypes, locations, createDevice, createLocation, createDeviceType } = useDevices();
  const [activeStep, setActiveStep] = useState(0);
  const [scanning, setScanning] = useState(false);
  const [foundDevices, setFoundDevices] = useState([]);
  const [selectedDevices, setSelectedDevices] = useState([]);
  const [quickLocation, setQuickLocation] = useState('');
  const [showNewLocationForm, setShowNewLocationForm] = useState(false);
  const [newLocationName, setNewLocationName] = useState('');

  // Pre-configured device templates for common scenarios
  const deviceTemplates = [
    {
      id: 'living-room-starter',
      name: 'Living Room Starter Kit',
      description: 'Basic living room setup with lights and switches',
      devices: [
        { name: 'Living Room Light', type: 'Smart Light', location: 'Living Room' },
        { name: 'Table Lamp', type: 'Smart Plug', location: 'Living Room' },
        { name: 'Main Switch', type: 'Smart Switch', location: 'Living Room' }
      ]
    },
    {
      id: 'bedroom-comfort',
      name: 'Bedroom Comfort',
      description: 'Bedroom setup with temperature control and lighting',
      devices: [
        { name: 'Bedroom Light', type: 'Smart Light', location: 'Bedroom' },
        { name: 'Bedside Lamp', type: 'Smart Light', location: 'Bedroom' },
        { name: 'Temperature Sensor', type: 'Temperature Sensor', location: 'Bedroom' }
      ]
    },
    {
      id: 'security-basic',
      name: 'Basic Security',
      description: 'Entry points monitoring with door and motion sensors',
      devices: [
        { name: 'Front Door Sensor', type: 'Door Sensor', location: 'Entry' },
        { name: 'Motion Detector', type: 'Motion Sensor', location: 'Entry' },
        { name: 'Security Light', type: 'Smart Light', location: 'Entry' }
      ]
    }
  ];

  const getDeviceIcon = (typeName) => {
    switch (typeName) {
      case 'Smart Light':
        return <Lightbulb />;
      case 'Temperature Sensor':
        return <Thermostat />;
      case 'Door Sensor':
      case 'Motion Sensor':
        return <Security />;
      case 'Smart Switch':
      case 'Smart Plug':
        return <Power />;
      default:
        return <Devices />;
    }
  };

  const simulateDeviceDiscovery = async () => {
    setScanning(true);
    
    try {
      // Call real network scanner service
      const response = await fetch('http://localhost:3005/api/scan/network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setFoundDevices(data.devices || []);
        
        if (data.devices && data.devices.length > 0) {
          toast.success(`Found ${data.devices.length} devices on network`);
        } else {
          toast.info('No devices found on network. Make sure IoT devices are powered on and connected.');
        }
      } else {
        throw new Error('Scanner service unavailable');
      }
    } catch (error) {
      console.error('Network scan error:', error);
      
      // Fallback to manual entry message
      setFoundDevices([]);
      toast.error('Network scanner unavailable. Please add devices manually using "Add Device" button.');
    } finally {
      setScanning(false);
    }
  };

  const handleDeviceSelection = (device) => {
    setSelectedDevices(prev => {
      const exists = prev.find(d => d.id === device.id);
      if (exists) {
        return prev.filter(d => d.id !== device.id);
      }
      return [...prev, device];
    });
  };

  const handleTemplateSelect = async (template) => {
    try {
      for (const deviceConfig of template.devices) {
        const deviceType = deviceTypes.find(dt => dt.name === deviceConfig.type);
        let locationId = locations.find(l => l.name === deviceConfig.location)?.id;
        
        // Create location if it doesn't exist
        if (!locationId) {
          const newLocation = await createLocation({ name: deviceConfig.location });
          locationId = newLocation.id;
        }
        
        await createDevice({
          name: deviceConfig.name,
          device_id: `${deviceConfig.name.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`,
          device_type_id: deviceType.id,
          location_id: locationId
        });
      }
      
      toast.success(`${template.name} devices added successfully!`);
      onClose();
    } catch (error) {
      console.error('Failed to create template devices:', error);
      toast.error('Failed to create template devices');
    }
  };

  const handleQuickLocationCreate = async () => {
    try {
      await createLocation({ name: newLocationName });
      setNewLocationName('');
      setShowNewLocationForm(false);
      toast.success('Location created successfully!');
    } catch (error) {
      console.error('Failed to create location:', error);
      toast.error('Failed to create location');
    }
  };

  const handleSelectedDevicesAdd = async () => {
    if (!quickLocation) {
      toast.error('Please select a location first');
      return;
    }

    try {
      for (const device of selectedDevices) {
        let deviceType = deviceTypes.find(dt => dt.name === device.type);
        
        // If device type doesn't exist, create a generic "Unknown Device" type
        if (!deviceType) {
          try {
            const deviceTypeName = device.type === "Unknown" ? "Unknown Device" : device.type;
            
            // Check if this device type already exists (case-insensitive)
            const existingDeviceType = deviceTypes.find(dt => 
              dt.name.toLowerCase() === deviceTypeName.toLowerCase()
            );
            
            if (existingDeviceType) {
              deviceType = existingDeviceType;
            } else {
              // Create new device type with a unique name if necessary
              let uniqueName = deviceTypeName;
              let counter = 1;
              while (deviceTypes.find(dt => dt.name.toLowerCase() === uniqueName.toLowerCase())) {
                uniqueName = `${deviceTypeName} ${counter}`;
                counter++;
              }
              
              deviceType = await createDeviceType({
                name: uniqueName,
                description: `Auto-created device type for ${device.type} from network scan`,
                manufacturer: device.manufacturer || "Unknown",
                model: device.model || "Unknown",
                category: "Other",
                capabilities: ["basic"],
                default_config: {
                  discovered_from_network: true,
                  discovery_method: device.discovery_method || "network_scan"
                }
              });
            }
          } catch (error) {
            console.error('Failed to create device type:', error);
            // Fallback to first available device type or Unknown Device type
            deviceType = deviceTypes.find(dt => dt.name === "Unknown Device") || deviceTypes[0];
          }
        }
        
        await createDevice({
          name: device.name,
          device_id: device.id,
          device_type_id: deviceType.id,
          location_id: quickLocation,
          mac_address: device.mac,
          ip_address: device.ip
        });
      }
      
      toast.success(`${selectedDevices.length} devices added successfully!`);
      onClose();
    } catch (error) {
      console.error('Failed to add devices:', error);
      toast.error('Failed to add devices');
    }
  };

  const steps = [
    {
      label: 'Choose Setup Method',
      content: (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Search sx={{ mr: 1 }} />
                  <Typography variant="h6">Auto-Discovery</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Automatically scan your network for smart devices
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  variant="contained"
                  onClick={() => {
                    setActiveStep(1);
                    simulateDeviceDiscovery();
                  }}
                  startIcon={<Wifi />}
                >
                  Scan Network
                </Button>
              </CardActions>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Devices sx={{ mr: 1 }} />
                  <Typography variant="h6">Quick Templates</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Use pre-configured device setups for common scenarios
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  variant="outlined"
                  onClick={() => setActiveStep(2)}
                >
                  Browse Templates
                </Button>
              </CardActions>
            </Card>
          </Grid>
        </Grid>
      )
    },
    {
      label: 'Select Discovered Devices',
      content: (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Found {foundDevices.length} devices</Typography>
            <Button
              startIcon={<Refresh />}
              onClick={simulateDeviceDiscovery}
              disabled={scanning}
            >
              Rescan
            </Button>
          </Box>
          
          {scanning && (
            <Box sx={{ mb: 3 }}>
              <LinearProgress />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Scanning network for devices...
              </Typography>
            </Box>
          )}
          
          <Grid container spacing={2}>
            {foundDevices.map((device) => (
              <Grid item xs={12} sm={6} md={4} key={device.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    border: selectedDevices.find(d => d.id === device.id) ? '2px solid' : '1px solid',
                    borderColor: selectedDevices.find(d => d.id === device.id) ? 'primary.main' : 'divider'
                  }}
                  onClick={() => handleDeviceSelection(device)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {getDeviceIcon(device.type)}
                      <Typography variant="subtitle1" sx={{ ml: 1 }}>
                        {device.name}
                      </Typography>
                      {selectedDevices.find(d => d.id === device.id) && (
                        <CheckCircle color="primary" sx={{ ml: 'auto' }} />
                      )}
                    </Box>
                    <Chip label={device.type} size="small" sx={{ mb: 1 }} />
                    <Typography variant="body2" color="text.secondary">
                      {device.manufacturer} {device.model}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      IP: {device.ip}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          
          {selectedDevices.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Assign Location ({selectedDevices.length} devices selected)
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel>Select Location</InputLabel>
                  <Select
                    value={quickLocation}
                    onChange={(e) => setQuickLocation(e.target.value)}
                    label="Select Location"
                  >
                    {locations.map((location) => (
                      <MenuItem key={location.id} value={location.id}>
                        {location.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <Button
                  variant="outlined"
                  onClick={() => setShowNewLocationForm(true)}
                >
                  New Location
                </Button>
              </Box>
              
              {showNewLocationForm && (
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
                  <TextField
                    label="Location Name"
                    value={newLocationName}
                    onChange={(e) => setNewLocationName(e.target.value)}
                    size="small"
                  />
                  <Button
                    variant="contained"
                    onClick={handleQuickLocationCreate}
                    disabled={!newLocationName.trim()}
                  >
                    Create
                  </Button>
                  <IconButton onClick={() => setShowNewLocationForm(false)}>
                    <Close />
                  </IconButton>
                </Box>
              )}
              
              <Button
                variant="contained"
                onClick={handleSelectedDevicesAdd}
                disabled={!quickLocation}
                size="large"
              >
                Add {selectedDevices.length} Devices
              </Button>
            </Box>
          )}
        </Box>
      )
    },
    {
      label: 'Choose Template',
      content: (
        <Grid container spacing={3}>
          {deviceTemplates.map((template) => (
            <Grid item xs={12} md={6} key={template.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {template.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {template.description}
                  </Typography>
                  
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    Includes:
                  </Typography>
                  {template.devices.map((device, index) => (
                    <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {getDeviceIcon(device.type)}
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {device.name} ({device.type})
                      </Typography>
                    </Box>
                  ))}
                </CardContent>
                <CardActions>
                  <Button
                    variant="contained"
                    onClick={() => handleTemplateSelect(template)}
                    fullWidth
                  >
                    Use This Template
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )
    }
  ];

  if (!open) return null;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3, position: 'relative' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">Quick Device Setup</Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          This wizard will help you quickly add devices to your home automation system
        </Alert>
        
        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel>{step.label}</StepLabel>
              <StepContent>
                {step.content}
                
                {index > 0 && (
                  <Box sx={{ mb: 2, mt: 2 }}>
                    <Button
                      variant="outlined"
                      onClick={() => setActiveStep(index - 1)}
                    >
                      Back
                    </Button>
                  </Box>
                )}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>
    </Container>
  );
};

export default QuickDeviceSetup;