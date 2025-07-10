import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Box,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Alert
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Devices,
  Lightbulb,
  Thermostat,
  Security,
  Power,
  FavoriteOutlined,
  DirectionsRun,
  MonitorWeight,
  LocalHospital,
  Bloodtype,
  Bedtime,
  Air
} from '@mui/icons-material';
import { useDevices } from '../contexts/DeviceContext';
import { useAuth } from '../contexts/AuthContext';

const DeviceTypes = () => {
  const { deviceTypes, createDeviceType, fetchDeviceTypes } = useDevices();
  const { isAdmin } = useAuth();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedDeviceType, setSelectedDeviceType] = useState(null);
  const [deviceTypeForm, setDeviceTypeForm] = useState({
    name: '',
    description: '',
    manufacturer: '',
    model: '',
    category: '',
    capabilities: [],
    default_config: {}
  });

  const deviceCategories = [
    'Smart Light',
    'Smart Switch', 
    'Sensor',
    'Smart Plug',
    'Security',
    'Climate',
    'Entertainment',
    // Health & Fitness Categories
    'Fitness Tracker',
    'Health Monitor',
    'Smart Scale',
    'Blood Pressure Monitor',
    'Sleep Tracker',
    'Air Quality Monitor',
    'Medical Alert Device',
    'Other'
  ];

  const availableCapabilities = [
    // Traditional home automation capabilities
    'switch',
    'dimmer',
    'color',
    'temperature',
    'humidity',
    'motion',
    'door',
    'window',
    'lock',
    'camera',
    'speaker',
    'microphone',
    // Health & Fitness capabilities
    'heart_rate',
    'blood_pressure',
    'oxygen_saturation',
    'body_temperature',
    'sleep_tracking',
    'step_counting',
    'calorie_tracking',
    'weight_measurement',
    'medication_reminder',
    'fall_detection',
    'emergency_alert',
    'workout_tracking',
    'stress_monitoring',
    'hydration_tracking'
  ];

  const getDeviceTypeIcon = (category) => {
    switch (category) {
      case 'Smart Light':
        return <Lightbulb />;
      case 'Sensor':
        return <Thermostat />;
      case 'Security':
        return <Security />;
      case 'Smart Switch':
      case 'Smart Plug':
        return <Power />;
      // Health & Fitness Icons
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

  const handleDialog = (deviceType = null) => {
    setSelectedDeviceType(deviceType);
    if (deviceType) {
      setDeviceTypeForm({
        name: deviceType.name,
        description: deviceType.description || '',
        manufacturer: deviceType.manufacturer || '',
        model: deviceType.model || '',
        category: deviceType.category || '',
        capabilities: deviceType.capabilities || [],
        default_config: deviceType.default_config || {}
      });
    } else {
      setDeviceTypeForm({
        name: '',
        description: '',
        manufacturer: '',
        model: '',
        category: '',
        capabilities: [],
        default_config: {}
      });
    }
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const formData = { ...deviceTypeForm };
      
      if (selectedDeviceType) {
        // Update functionality would go here
        console.log('Update not implemented yet');
      } else {
        await createDeviceType(formData);
      }
      setDialogOpen(false);
      resetForm();
    } catch (error) {
      console.error('Failed to save device type:', error);
    }
  };

  const resetForm = () => {
    setDeviceTypeForm({
      name: '',
      description: '',
      manufacturer: '',
      model: '',
      category: '',
      capabilities: [],
      default_config: {}
    });
    setSelectedDeviceType(null);
  };

  const handleCapabilityChange = (capability) => {
    const currentCapabilities = deviceTypeForm.capabilities;
    if (currentCapabilities.includes(capability)) {
      setDeviceTypeForm({
        ...deviceTypeForm,
        capabilities: currentCapabilities.filter(c => c !== capability)
      });
    } else {
      setDeviceTypeForm({
        ...deviceTypeForm,
        capabilities: [...currentCapabilities, capability]
      });
    }
  };

  if (!isAdmin()) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="warning">
          Admin access required to manage device types.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Device Types
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleDialog()}
        >
          Add Device Type
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Icon</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Manufacturer</TableCell>
              <TableCell>Model</TableCell>
              <TableCell>Capabilities</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {deviceTypes.map((deviceType) => (
              <TableRow key={deviceType.id}>
                <TableCell>
                  {getDeviceTypeIcon(deviceType.category)}
                </TableCell>
                <TableCell>
                  <Typography variant="subtitle1">
                    {deviceType.name}
                  </Typography>
                  {deviceType.description && (
                    <Typography variant="body2" color="text.secondary">
                      {deviceType.description}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>{deviceType.category}</TableCell>
                <TableCell>{deviceType.manufacturer || '-'}</TableCell>
                <TableCell>{deviceType.model || '-'}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {(deviceType.capabilities || []).map((capability) => (
                      <Chip
                        key={capability}
                        label={capability}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleDialog(deviceType)}
                  >
                    <Edit />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => {
                      if (window.confirm('Are you sure you want to delete this device type?')) {
                        console.log('Delete not implemented yet');
                      }
                    }}
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Device Type Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedDeviceType ? 'Edit Device Type' : 'Add Device Type'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Name"
            fullWidth
            variant="outlined"
            value={deviceTypeForm.name}
            onChange={(e) => setDeviceTypeForm({ ...deviceTypeForm, name: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={2}
            variant="outlined"
            value={deviceTypeForm.description}
            onChange={(e) => setDeviceTypeForm({ ...deviceTypeForm, description: e.target.value })}
            sx={{ mb: 2 }}
          />

          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label="Manufacturer"
              fullWidth
              variant="outlined"
              value={deviceTypeForm.manufacturer}
              onChange={(e) => setDeviceTypeForm({ ...deviceTypeForm, manufacturer: e.target.value })}
            />
            <TextField
              label="Model"
              fullWidth
              variant="outlined"
              value={deviceTypeForm.model}
              onChange={(e) => setDeviceTypeForm({ ...deviceTypeForm, model: e.target.value })}
            />
          </Box>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={deviceTypeForm.category}
              onChange={(e) => setDeviceTypeForm({ ...deviceTypeForm, category: e.target.value })}
              label="Category"
            >
              {deviceCategories.map((category) => (
                <MenuItem key={category} value={category}>
                  {category}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Typography variant="subtitle1" sx={{ mb: 1 }}>
            Capabilities
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {availableCapabilities.map((capability) => (
              <FormControlLabel
                key={capability}
                control={
                  <Checkbox
                    checked={deviceTypeForm.capabilities.includes(capability)}
                    onChange={() => handleCapabilityChange(capability)}
                  />
                }
                label={capability}
              />
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!deviceTypeForm.name.trim() || !deviceTypeForm.category}
          >
            {selectedDeviceType ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DeviceTypes;