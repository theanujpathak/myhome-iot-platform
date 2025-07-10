import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  IconButton,
  Switch,
  Slider,
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
  Button,
  Divider,
  LinearProgress,
  Alert
} from '@mui/material';
import {
  Memory,
  ExpandMore,
  Edit,
  Delete,
  Wifi,
  WifiOff,
  Lightbulb,
  Thermostat,
  Security,
  Power,
  Sensors,
  Settings,
  CloudUpload,
  Refresh
} from '@mui/icons-material';

const CompositeDeviceCard = ({ device, onEdit, onDelete, onCommand }) => {
  const [expanded, setExpanded] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Parse device config to get pin information
  const pinConfig = device.device_config?.pins || [];
  const firmwareVersion = device.device_config?.firmware_version || 'Unknown';
  
  // Mock sub-device states (in real implementation, this would come from device.sub_devices)
  const subDeviceStates = {
    2: { value: 'true', type: 'digital' },
    4: { value: 'false', type: 'digital' },
    32: { value: '23.5', type: 'analog' },
    33: { value: '65', type: 'analog' }
  };

  const getFunctionIcon = (functionType) => {
    switch (functionType) {
      case 'light':
        return <Lightbulb color="warning" />;
      case 'temperature':
        return <Thermostat color="info" />;
      case 'motion':
      case 'door':
        return <Security color="error" />;
      case 'switch':
      case 'relay':
        return <Power color="success" />;
      case 'servo':
        return <Settings color="primary" />;
      default:
        return <Sensors color="primary" />;
    }
  };

  const handlePinCommand = async (pin, command, value) => {
    try {
      await onCommand(device.id, `pin_${pin}_${command}`, { value });
    } catch (error) {
      console.error('Failed to send pin command:', error);
    }
  };

  const handleRefreshDevice = async () => {
    setRefreshing(true);
    try {
      await onCommand(device.id, 'refresh_status', {});
    } catch (error) {
      console.error('Failed to refresh device:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const getOnlinePinCount = () => {
    return pinConfig.filter(pin => pin.enabled).length;
  };

  const getActivePinCount = () => {
    return pinConfig.filter(pin => {
      const state = subDeviceStates[pin.pin];
      return state && (state.value === 'true' || parseFloat(state.value) > 0);
    }).length;
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Memory sx={{ mr: 1, color: 'primary.main' }} />
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" component="h2">
              {device.name}
            </Typography>
            <Typography color="text.secondary" variant="body2">
              ESP32 • {getOnlinePinCount()} pins • {getActivePinCount()} active
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              icon={device.is_online ? <Wifi /> : <WifiOff />}
              label={device.is_online ? 'Online' : 'Offline'}
              color={device.is_online ? 'success' : 'error'}
              size="small"
            />
            <IconButton size="small" onClick={handleRefreshDevice} disabled={refreshing}>
              <Refresh />
            </IconButton>
            <IconButton size="small" onClick={() => onEdit(device)}>
              <Edit />
            </IconButton>
            <IconButton size="small" onClick={() => onDelete(device.id)}>
              <Delete />
            </IconButton>
          </Box>
        </Box>

        {/* Device Summary */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            <strong>MAC:</strong> {device.mac_address || 'N/A'} • 
            <strong>IP:</strong> {device.ip_address || 'N/A'} • 
            <strong>Firmware:</strong> {firmwareVersion}
          </Typography>
          {device.description && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {device.description}
            </Typography>
          )}
        </Box>

        {refreshing && <LinearProgress sx={{ mb: 2 }} />}

        {/* Pin Status Overview */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Pin Status Overview
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {pinConfig.map((pin) => {
              const state = subDeviceStates[pin.pin];
              const isActive = state && (state.value === 'true' || parseFloat(state.value) > 0);
              
              return (
                <Chip
                  key={pin.pin}
                  icon={getFunctionIcon(pin.function)}
                  label={`GPIO${pin.pin}`}
                  size="small"
                  color={isActive ? 'primary' : 'default'}
                  variant={isActive ? 'filled' : 'outlined'}
                />
              );
            })}
          </Box>
        </Box>

        {/* Expandable Pin Details */}
        <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="subtitle2">
              Pin Configuration & Controls ({pinConfig.length} pins)
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Pin</TableCell>
                    <TableCell>Function</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Value</TableCell>
                    <TableCell>Control</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pinConfig.map((pin) => {
                    const state = subDeviceStates[pin.pin];
                    const currentValue = state?.value || '0';
                    
                    return (
                      <TableRow key={pin.pin}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {getFunctionIcon(pin.function)}
                            <Typography variant="body2" sx={{ ml: 1 }}>
                              GPIO {pin.pin}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{pin.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {pin.function}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={pin.type} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {pin.type === 'analog_input' ? `${currentValue}V` : currentValue}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {pin.type === 'digital_output' && (
                            <Switch
                              checked={currentValue === 'true'}
                              onChange={(e) => handlePinCommand(pin.pin, 'set', e.target.checked)}
                              disabled={!device.is_online}
                              size="small"
                            />
                          )}
                          {pin.type === 'pwm_output' && (
                            <Box sx={{ width: 100 }}>
                              <Slider
                                value={parseInt(currentValue) || 0}
                                onChange={(e, value) => handlePinCommand(pin.pin, 'set', value)}
                                min={0}
                                max={255}
                                disabled={!device.is_online}
                                size="small"
                              />
                            </Box>
                          )}
                          {pin.type === 'digital_input' && (
                            <Chip
                              label={currentValue === 'true' ? 'HIGH' : 'LOW'}
                              color={currentValue === 'true' ? 'success' : 'default'}
                              size="small"
                            />
                          )}
                          {pin.type === 'analog_input' && (
                            <Typography variant="body2" color="text.secondary">
                              Read-only
                            </Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>

        {/* Device Actions */}
        <Box sx={{ mt: 2 }}>
          <Divider sx={{ my: 1 }} />
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              size="small"
              startIcon={<CloudUpload />}
              onClick={() => onCommand(device.id, 'ota_update', {})}
              disabled={!device.is_online}
            >
              Update Firmware
            </Button>
            <Button
              size="small"
              startIcon={<Refresh />}
              onClick={() => onCommand(device.id, 'restart', {})}
              disabled={!device.is_online}
            >
              Restart
            </Button>
            <Button
              size="small"
              startIcon={<Settings />}
              onClick={() => onCommand(device.id, 'factory_reset', {})}
              disabled={!device.is_online}
            >
              Factory Reset
            </Button>
          </Box>
        </Box>

        {/* Last seen */}
        {device.last_seen && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Last seen: {new Date(device.last_seen).toLocaleString()}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default CompositeDeviceCard;