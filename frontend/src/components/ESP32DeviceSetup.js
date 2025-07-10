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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  FormControlLabel,
  Divider,
  Alert
} from '@mui/material';
import {
  Memory,
  Add,
  Delete,
  ExpandMore,
  Close,
  Lightbulb,
  Thermostat,
  Security,
  Power,
  Sensors,
  ElectricBolt,
  Settings
} from '@mui/icons-material';
import { useDevices } from '../contexts/DeviceContext';
import { toast } from 'react-toastify';

const ESP32DeviceSetup = ({ open, onClose }) => {
  const { locations, createDevice, createDeviceType } = useDevices();
  const [esp32Config, setEsp32Config] = useState({
    name: '',
    location_id: '',
    mac_address: '',
    ip_address: '',
    description: '',
    firmware_version: '1.0.0',
    pins: []
  });

  // ESP32 Pin Configuration
  const esp32Pins = {
    digital: [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
    analog: [32, 33, 34, 35, 36, 37, 38, 39], // ADC1 and ADC2 pins
    pwm: [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33],
    i2c: [21, 22], // Default SDA, SCL
    spi: [5, 18, 19, 23], // Default SPI pins
    uart: [1, 3, 16, 17] // TX, RX pins
  };

  const pinTypes = [
    { value: 'digital_input', label: 'Digital Input', icon: <ElectricBolt /> },
    { value: 'digital_output', label: 'Digital Output', icon: <ElectricBolt /> },
    { value: 'analog_input', label: 'Analog Input', icon: <Sensors /> },
    { value: 'pwm_output', label: 'PWM Output', icon: <Settings /> },
    { value: 'i2c', label: 'I2C', icon: <Memory /> },
    { value: 'spi', label: 'SPI', icon: <Memory /> }
  ];

  const deviceFunctions = [
    { value: 'light', label: 'Light Control', icon: <Lightbulb />, defaultPin: 'digital_output' },
    { value: 'switch', label: 'Switch/Button', icon: <Power />, defaultPin: 'digital_input' },
    { value: 'temperature', label: 'Temperature Sensor', icon: <Thermostat />, defaultPin: 'analog_input' },
    { value: 'humidity', label: 'Humidity Sensor', icon: <Sensors />, defaultPin: 'analog_input' },
    { value: 'motion', label: 'Motion Sensor', icon: <Security />, defaultPin: 'digital_input' },
    { value: 'door', label: 'Door/Window Sensor', icon: <Security />, defaultPin: 'digital_input' },
    { value: 'relay', label: 'Relay Control', icon: <Power />, defaultPin: 'digital_output' },
    { value: 'servo', label: 'Servo Motor', icon: <Settings />, defaultPin: 'pwm_output' },
    { value: 'led_strip', label: 'LED Strip', icon: <Lightbulb />, defaultPin: 'pwm_output' },
    { value: 'buzzer', label: 'Buzzer/Alarm', icon: <Sensors />, defaultPin: 'digital_output' }
  ];

  const esp32Templates = [
    {
      id: 'basic_room_controller',
      name: 'Basic Room Controller',
      description: 'Light, temperature sensor, motion detector',
      pins: [
        { pin: 2, type: 'digital_output', function: 'light', name: 'Room Light' },
        { pin: 34, type: 'analog_input', function: 'temperature', name: 'Temperature Sensor' },
        { pin: 4, type: 'digital_input', function: 'motion', name: 'Motion Detector' }
      ]
    },
    {
      id: 'smart_switch_panel',
      name: 'Smart Switch Panel',
      description: '4 switches controlling 4 lights',
      pins: [
        { pin: 5, type: 'digital_input', function: 'switch', name: 'Switch 1' },
        { pin: 18, type: 'digital_input', function: 'switch', name: 'Switch 2' },
        { pin: 19, type: 'digital_input', function: 'switch', name: 'Switch 3' },
        { pin: 21, type: 'digital_input', function: 'switch', name: 'Switch 4' },
        { pin: 2, type: 'digital_output', function: 'light', name: 'Light 1' },
        { pin: 4, type: 'digital_output', function: 'light', name: 'Light 2' },
        { pin: 16, type: 'digital_output', function: 'light', name: 'Light 3' },
        { pin: 17, type: 'digital_output', function: 'light', name: 'Light 4' }
      ]
    },
    {
      id: 'security_node',
      name: 'Security Node',
      description: 'Door sensor, motion detector, alarm buzzer',
      pins: [
        { pin: 12, type: 'digital_input', function: 'door', name: 'Door Sensor' },
        { pin: 13, type: 'digital_input', function: 'motion', name: 'Motion Detector' },
        { pin: 14, type: 'digital_output', function: 'buzzer', name: 'Alarm Buzzer' },
        { pin: 15, type: 'digital_output', function: 'light', name: 'Security Light' }
      ]
    },
    {
      id: 'environmental_monitor',
      name: 'Environmental Monitor',
      description: 'Temperature, humidity, light sensor with fan control',
      pins: [
        { pin: 32, type: 'analog_input', function: 'temperature', name: 'Temperature' },
        { pin: 33, type: 'analog_input', function: 'humidity', name: 'Humidity' },
        { pin: 34, type: 'analog_input', function: 'light', name: 'Light Level' },
        { pin: 25, type: 'pwm_output', function: 'relay', name: 'Fan Control' }
      ]
    }
  ];

  const addPinConfiguration = () => {
    const newPin = {
      id: Date.now(),
      pin: '',
      type: 'digital_input',
      function: 'light',
      name: '',
      enabled: true,
      config: {}
    };
    setEsp32Config({
      ...esp32Config,
      pins: [...esp32Config.pins, newPin]
    });
  };

  const removePinConfiguration = (pinId) => {
    setEsp32Config({
      ...esp32Config,
      pins: esp32Config.pins.filter(p => p.id !== pinId)
    });
  };

  const updatePinConfiguration = (pinId, field, value) => {
    setEsp32Config({
      ...esp32Config,
      pins: esp32Config.pins.map(p => 
        p.id === pinId ? { ...p, [field]: value } : p
      )
    });
  };

  const applyTemplate = (template) => {
    const templatePins = template.pins.map((pin, index) => ({
      id: Date.now() + index,
      pin: pin.pin,
      type: pin.type,
      function: pin.function,
      name: pin.name,
      enabled: true,
      config: {}
    }));
    
    setEsp32Config({
      ...esp32Config,
      pins: templatePins
    });
  };

  const validatePinConfiguration = () => {
    const usedPins = new Set();
    const errors = [];

    esp32Config.pins.forEach((pinConfig, index) => {
      // Check for duplicate pins
      if (usedPins.has(pinConfig.pin)) {
        errors.push(`Pin ${pinConfig.pin} is used multiple times`);
      }
      usedPins.add(pinConfig.pin);

      // Check if pin is valid for the selected type
      if (pinConfig.type === 'analog_input' && !esp32Pins.analog.includes(pinConfig.pin)) {
        errors.push(`Pin ${pinConfig.pin} cannot be used for analog input`);
      }

      // Check if pin name is provided
      if (!pinConfig.name.trim()) {
        errors.push(`Pin ${pinConfig.pin} needs a name`);
      }
    });

    return errors;
  };

  const handleCreateESP32Device = async () => {
    if (!esp32Config.name || !esp32Config.location_id) {
      toast.error('Please enter device name and select location');
      return;
    }

    const validationErrors = validatePinConfiguration();
    if (validationErrors.length > 0) {
      toast.error(`Configuration errors: ${validationErrors.join(', ')}`);
      return;
    }

    try {
      // Create a composite device type for this ESP32
      const deviceType = await createDeviceType({
        name: `ESP32 - ${esp32Config.name}`,
        description: `ESP32 microcontroller with ${esp32Config.pins.length} configured pins`,
        manufacturer: 'Espressif',
        model: 'ESP32',
        category: 'Microcontroller',
        capabilities: ['composite', 'mqtt', 'ota'],
        default_config: {
          pins: esp32Config.pins,
          firmware_version: esp32Config.firmware_version
        }
      });

      // Create the main ESP32 device
      const mainDevice = await createDevice({
        name: esp32Config.name,
        device_id: `esp32_${esp32Config.name.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`,
        device_type_id: deviceType.id,
        location_id: esp32Config.location_id,
        mac_address: esp32Config.mac_address,
        ip_address: esp32Config.ip_address,
        description: esp32Config.description,
        device_config: {
          pins: esp32Config.pins,
          firmware_version: esp32Config.firmware_version
        }
      });

      // Create virtual sub-devices for each pin function
      for (const pinConfig of esp32Config.pins) {
        if (pinConfig.enabled && pinConfig.name) {
          const subDeviceType = deviceFunctions.find(f => f.value === pinConfig.function);
          if (subDeviceType) {
            await createDevice({
              name: pinConfig.name,
              device_id: `${mainDevice.device_id}_pin_${pinConfig.pin}`,
              device_type_id: deviceType.id, // We could create separate types for each function
              location_id: esp32Config.location_id,
              parent_device_id: mainDevice.id,
              device_config: {
                pin: pinConfig.pin,
                pin_type: pinConfig.type,
                function: pinConfig.function,
                parent_device: mainDevice.device_id
              }
            });
          }
        }
      }

      toast.success(`ESP32 device with ${esp32Config.pins.length} pins created successfully!`);
      onClose();
    } catch (error) {
      console.error('Failed to create ESP32 device:', error);
      toast.error('Failed to create ESP32 device');
    }
  };

  const getAvailablePins = (pinType) => {
    const usedPins = new Set(esp32Config.pins.map(p => p.pin));
    switch (pinType) {
      case 'analog_input':
        return esp32Pins.analog.filter(pin => !usedPins.has(pin));
      case 'pwm_output':
        return esp32Pins.pwm.filter(pin => !usedPins.has(pin));
      default:
        return esp32Pins.digital.filter(pin => !usedPins.has(pin));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Memory />
          ESP32 Device Setup
          <IconButton onClick={onClose} sx={{ ml: 'auto' }}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {/* Basic Device Info */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Device Name"
              value={esp32Config.name}
              onChange={(e) => setEsp32Config({...esp32Config, name: e.target.value})}
              placeholder="e.g., Living Room Controller"
              sx={{ mb: 2 }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Location</InputLabel>
              <Select
                value={esp32Config.location_id}
                onChange={(e) => setEsp32Config({...esp32Config, location_id: e.target.value})}
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
        </Grid>

        {/* Quick Templates */}
        <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
          Quick Templates
        </Typography>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {esp32Templates.map((template) => (
            <Grid item xs={12} sm={6} md={3} key={template.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 3 },
                  height: '100%'
                }}
                onClick={() => applyTemplate(template)}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Memory sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                  <Typography variant="subtitle2" gutterBottom>
                    {template.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {template.description}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Chip label={`${template.pins.length} pins`} size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Pin Configuration */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Pin Configuration</Typography>
          <Button
            startIcon={<Add />}
            onClick={addPinConfiguration}
            variant="outlined"
          >
            Add Pin
          </Button>
        </Box>

        {esp32Config.pins.length > 0 && (
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Pin</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Function</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Enabled</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {esp32Config.pins.map((pinConfig) => (
                  <TableRow key={pinConfig.id}>
                    <TableCell>
                      <FormControl size="small" sx={{ minWidth: 80 }}>
                        <Select
                          value={pinConfig.pin}
                          onChange={(e) => updatePinConfiguration(pinConfig.id, 'pin', e.target.value)}
                        >
                          {getAvailablePins(pinConfig.type).map((pin) => (
                            <MenuItem key={pin} value={pin}>
                              GPIO {pin}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </TableCell>
                    <TableCell>
                      <FormControl size="small" sx={{ minWidth: 120 }}>
                        <Select
                          value={pinConfig.type}
                          onChange={(e) => updatePinConfiguration(pinConfig.id, 'type', e.target.value)}
                        >
                          {pinTypes.map((type) => (
                            <MenuItem key={type.value} value={type.value}>
                              {type.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </TableCell>
                    <TableCell>
                      <FormControl size="small" sx={{ minWidth: 120 }}>
                        <Select
                          value={pinConfig.function}
                          onChange={(e) => updatePinConfiguration(pinConfig.id, 'function', e.target.value)}
                        >
                          {deviceFunctions.map((func) => (
                            <MenuItem key={func.value} value={func.value}>
                              {func.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        value={pinConfig.name}
                        onChange={(e) => updatePinConfiguration(pinConfig.id, 'name', e.target.value)}
                        placeholder="Device name"
                      />
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={pinConfig.enabled}
                        onChange={(e) => updatePinConfiguration(pinConfig.id, 'enabled', e.target.checked)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => removePinConfiguration(pinConfig.id)}
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        {/* Advanced Configuration */}
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography>Advanced Configuration</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="MAC Address"
                  value={esp32Config.mac_address}
                  onChange={(e) => setEsp32Config({...esp32Config, mac_address: e.target.value})}
                  placeholder="XX:XX:XX:XX:XX:XX"
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="IP Address"
                  value={esp32Config.ip_address}
                  onChange={(e) => setEsp32Config({...esp32Config, ip_address: e.target.value})}
                  placeholder="192.168.1.100"
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Firmware Version"
                  value={esp32Config.firmware_version}
                  onChange={(e) => setEsp32Config({...esp32Config, firmware_version: e.target.value})}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  multiline
                  rows={3}
                  value={esp32Config.description}
                  onChange={(e) => setEsp32Config({...esp32Config, description: e.target.value})}
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Configuration Summary */}
        {esp32Config.pins.length > 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="subtitle2">Configuration Summary:</Typography>
            <Typography variant="body2">
              This ESP32 will control {esp32Config.pins.filter(p => p.enabled).length} devices across {esp32Config.pins.length} pins.
              Each pin will appear as a separate controllable device in your dashboard.
            </Typography>
          </Alert>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleCreateESP32Device}
          variant="contained"
          disabled={!esp32Config.name || !esp32Config.location_id || esp32Config.pins.length === 0}
        >
          Create ESP32 Device
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ESP32DeviceSetup;