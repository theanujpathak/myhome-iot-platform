import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Alert,
  LinearProgress,
  Fab,
  Badge,
  Tooltip,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Add,
  Upload,
  QrCode,
  Download,
  Visibility,
  Refresh,
  CloudUpload,
  Assignment,
  DevicesOther,
  Print,
  Batch,
  CheckCircle,
  Error,
  Warning,
  Info
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import axios from 'axios';

const ProvisioningManagement = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [batchDevices, setBatchDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [qrDialogOpen, setQrDialogOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const [bulkForm, setBulkForm] = useState({
    batch_name: '',
    manufacturer: 'Espressif',
    device_model: 'ESP32-WROOM-32',
    firmware_version: '1.0.0',
    installer_id: '',
    notes: ''
  });

  useEffect(() => {
    fetchProvisioningBatches();
  }, []);

  const fetchProvisioningBatches = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:3002/api/admin/provisioning/batches');
      setBatches(response.data);
    } catch (error) {
      console.error('Failed to fetch batches:', error);
      toast.error('Failed to load provisioning batches');
    } finally {
      setLoading(false);
    }
  };

  const fetchBatchDevices = async (batchId) => {
    try {
      const response = await axios.get(`http://localhost:3002/api/admin/provisioning/batches/${batchId}/devices`);
      setBatchDevices(response.data);
    } catch (error) {
      console.error('Failed to fetch batch devices:', error);
      toast.error('Failed to load batch devices');
    }
  };

  const handleBatchSelect = (batch) => {
    setSelectedBatch(batch);
    fetchBatchDevices(batch.batch_id);
  };

  const handleBulkProvision = async () => {
    if (!csvFile && (!bulkForm.batch_name || !sampleDevices.length)) {
      toast.error('Please provide batch details and devices');
      return;
    }

    try {
      setLoading(true);

      // Create sample bulk provisioning request
      const bulkData = {
        batch_name: bulkForm.batch_name,
        manufacturer: bulkForm.manufacturer,
        device_model: bulkForm.device_model,
        firmware_version: bulkForm.firmware_version,
        installer_id: bulkForm.installer_id,
        notes: bulkForm.notes,
        devices: sampleDevices
      };

      const response = await axios.post('http://localhost:3002/api/admin/provisioning/bulk', bulkData);
      
      if (response.data.success) {
        toast.success(`Successfully provisioned ${response.data.created_devices.length} devices`);
        setBulkDialogOpen(false);
        fetchProvisioningBatches();
        resetBulkForm();
      } else {
        toast.error('Bulk provisioning completed with errors');
      }

      if (response.data.errors && response.data.errors.length > 0) {
        response.data.errors.forEach(error => toast.error(error));
      }

    } catch (error) {
      console.error('Bulk provisioning failed:', error);
      toast.error(error.response?.data?.detail || 'Bulk provisioning failed');
    } finally {
      setLoading(false);
    }
  };

  const handleShowQRCode = async (device) => {
    try {
      const response = await axios.get(`http://localhost:3002/api/admin/provisioning/qr/${device.device_uid}`);
      setSelectedDevice({
        ...device,
        qr_code_url: response.data.qr_code_url,
        qr_code_data: response.data.qr_code_data
      });
      setQrDialogOpen(true);
    } catch (error) {
      console.error('Failed to fetch QR code:', error);
      toast.error('Failed to load QR code');
    }
  };

  const resetBulkForm = () => {
    setBulkForm({
      batch_name: '',
      manufacturer: 'Espressif',
      device_model: 'ESP32-WROOM-32',
      firmware_version: '1.0.0',
      installer_id: '',
      notes: ''
    });
    setCsvFile(null);
  };

  const downloadSampleCSV = () => {
    const csvContent = `device_name,device_model,mac_address,manufacturer,firmware_version,description
Smart Light 001,ESP32-WROOM-32,AA:BB:CC:DD:EE:10,Espressif,1.0.0,Living room smart light
Smart Light 002,ESP32-WROOM-32,AA:BB:CC:DD:EE:11,Espressif,1.0.0,Bedroom smart light
Smart Switch 001,ESP32-WROOM-32,AA:BB:CC:DD:EE:12,Espressif,1.0.0,Main power switch
Temperature Sensor 001,ESP32-WROOM-32,AA:BB:CC:DD:EE:13,Espressif,1.0.0,Living room temperature
Motion Sensor 001,ESP32-WROOM-32,AA:BB:CC:DD:EE:14,Espressif,1.0.0,Entry motion detector`;

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_devices.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const printQRCode = () => {
    if (selectedDevice && selectedDevice.qr_code_url) {
      const printWindow = window.open('', '_blank');
      printWindow.document.write(`
        <html>
          <head>
            <title>QR Code - ${selectedDevice.device_name}</title>
            <style>
              body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
              .qr-container { margin: 20px auto; max-width: 400px; }
              .device-info { margin: 20px 0; }
              .qr-code { max-width: 100%; height: auto; }
            </style>
          </head>
          <body>
            <div class="qr-container">
              <h2>${selectedDevice.device_name}</h2>
              <div class="device-info">
                <p><strong>Device ID:</strong> ${selectedDevice.device_id}</p>
                <p><strong>Device UID:</strong> ${selectedDevice.device_uid}</p>
                <p><strong>Model:</strong> ${selectedDevice.device_model}</p>
                <p><strong>MAC:</strong> ${selectedDevice.mac_address}</p>
              </div>
              <img src="${selectedDevice.qr_code_url}" alt="QR Code" class="qr-code" />
              <p><small>Scan this QR code to provision your device</small></p>
            </div>
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  // Sample devices for demonstration
  const sampleDevices = [
    {
      device_name: `Smart Light ${Date.now()}`,
      device_model: 'ESP32-WROOM-32',
      mac_address: `AA:BB:CC:DD:EE:${Math.floor(Math.random() * 100).toString().padStart(2, '0')}`,
      manufacturer: 'Espressif',
      description: 'Sample smart light for testing'
    },
    {
      device_name: `Temperature Sensor ${Date.now()}`,
      device_model: 'ESP32-WROOM-32',
      mac_address: `AA:BB:CC:DD:EF:${Math.floor(Math.random() * 100).toString().padStart(2, '0')}`,
      manufacturer: 'Espressif',
      description: 'Sample temperature sensor for testing'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'partial': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle />;
      case 'processing': return <Info />;
      case 'partial': return <Warning />;
      case 'failed': return <Error />;
      default: return <Info />;
    }
  };

  const renderBatchesTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6">Provisioning Batches</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={downloadSampleCSV}
          >
            Download CSV Template
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setBulkDialogOpen(true)}
          >
            Create Batch
          </Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Grid container spacing={3}>
        {batches.map((batch) => (
          <Grid item xs={12} md={6} lg={4} key={batch.id}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" noWrap>
                    {batch.batch_name}
                  </Typography>
                  <Chip
                    icon={getStatusIcon(batch.status)}
                    label={batch.status.toUpperCase()}
                    color={getStatusColor(batch.status)}
                    size="small"
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {batch.device_model} • {batch.manufacturer}
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Total:</strong> {batch.total_devices}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Provisioned:</strong> {batch.provisioned_devices}
                  </Typography>
                </Box>
                
                <Typography variant="caption" color="text.secondary">
                  Batch ID: {batch.batch_id}
                </Typography>
                
                <Typography variant="caption" color="text.secondary" display="block">
                  Created: {new Date(batch.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  startIcon={<Visibility />}
                  onClick={() => handleBatchSelect(batch)}
                >
                  View Devices
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {batches.length === 0 && !loading && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No provisioning batches found. Create your first batch to get started.
        </Alert>
      )}
    </Box>
  );

  const renderDevicesTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h6">
          {selectedBatch ? `Devices in ${selectedBatch.batch_name}` : 'Select a batch to view devices'}
        </Typography>
        {selectedBatch && (
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => fetchBatchDevices(selectedBatch.batch_id)}
          >
            Refresh
          </Button>
        )}
      </Box>

      {selectedBatch && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Batch Name</Typography>
                <Typography variant="body1">{selectedBatch.batch_name}</Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Status</Typography>
                <Chip
                  icon={getStatusIcon(selectedBatch.status)}
                  label={selectedBatch.status.toUpperCase()}
                  color={getStatusColor(selectedBatch.status)}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Progress</Typography>
                <Typography variant="body1">
                  {selectedBatch.provisioned_devices} / {selectedBatch.total_devices}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">Device Model</Typography>
                <Typography variant="body1">{selectedBatch.device_model}</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {batchDevices.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Device Name</TableCell>
                <TableCell>Device UID</TableCell>
                <TableCell>MAC Address</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {batchDevices.map((device) => (
                <TableRow key={device.id}>
                  <TableCell>{device.device_name}</TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {device.device_uid}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {device.mac_address}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={device.paired ? 'Paired' : 'Available'}
                      color={device.paired ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(device.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View QR Code">
                      <IconButton
                        size="small"
                        onClick={() => handleShowQRCode(device)}
                      >
                        <QrCode />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {selectedBatch && batchDevices.length === 0 && (
        <Alert severity="info">
          No devices found in this batch.
        </Alert>
      )}

      {!selectedBatch && (
        <Alert severity="info">
          Select a batch from the Batches tab to view its devices.
        </Alert>
      )}
    </Box>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Device Provisioning Management
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>New Feature:</strong> Bulk device provisioning with QR code generation and CSV import capabilities.
      </Alert>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assignment />
                Batches
                {batches.length > 0 && (
                  <Badge badgeContent={batches.length} color="primary" />
                )}
              </Box>
            }
          />
          <Tab
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DevicesOther />
                Devices
                {batchDevices.length > 0 && (
                  <Badge badgeContent={batchDevices.length} color="secondary" />
                )}
              </Box>
            }
          />
        </Tabs>
      </Box>

      {currentTab === 0 && renderBatchesTab()}
      {currentTab === 1 && renderDevicesTab()}

      {/* Bulk Provisioning Dialog */}
      <Dialog open={bulkDialogOpen} onClose={() => setBulkDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Provisioning Batch</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Batch Name"
                value={bulkForm.batch_name}
                onChange={(e) => setBulkForm({ ...bulkForm, batch_name: e.target.value })}
                placeholder="IoT Devices Batch 1"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Device Model</InputLabel>
                <Select
                  value={bulkForm.device_model}
                  onChange={(e) => setBulkForm({ ...bulkForm, device_model: e.target.value })}
                  label="Device Model"
                >
                  <MenuItem value="ESP32-WROOM-32">ESP32-WROOM-32</MenuItem>
                  <MenuItem value="ESP32-WROVER">ESP32-WROVER</MenuItem>
                  <MenuItem value="ESP8266">ESP8266</MenuItem>
                  <MenuItem value="ESP32-S2">ESP32-S2</MenuItem>
                  <MenuItem value="ESP32-S3">ESP32-S3</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Manufacturer"
                value={bulkForm.manufacturer}
                onChange={(e) => setBulkForm({ ...bulkForm, manufacturer: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Firmware Version"
                value={bulkForm.firmware_version}
                onChange={(e) => setBulkForm({ ...bulkForm, firmware_version: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Installer ID (Optional)"
                value={bulkForm.installer_id}
                onChange={(e) => setBulkForm({ ...bulkForm, installer_id: e.target.value })}
                placeholder="installer_001"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Notes (Optional)"
                value={bulkForm.notes}
                onChange={(e) => setBulkForm({ ...bulkForm, notes: e.target.value })}
                placeholder="Batch notes and deployment information..."
              />
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                <strong>Demo Mode:</strong> This will create a batch with 2 sample devices. 
                In production, you would upload a CSV file with your device list.
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleBulkProvision}
            variant="contained"
            disabled={loading || !bulkForm.batch_name}
            startIcon={loading ? <LinearProgress size={20} /> : <CloudUpload />}
          >
            {loading ? 'Creating...' : 'Create Batch'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* QR Code Dialog */}
      <Dialog open={qrDialogOpen} onClose={() => setQrDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Device QR Code</DialogTitle>
        <DialogContent>
          {selectedDevice && (
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                {selectedDevice.device_name}
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Device UID</Typography>
                <Typography variant="body1" fontFamily="monospace">
                  {selectedDevice.device_uid}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">Device ID</Typography>
                <Typography variant="body1" fontFamily="monospace">
                  {selectedDevice.device_id}
                </Typography>
              </Box>
              
              {selectedDevice.qr_code_url && (
                <Box sx={{ mb: 2 }}>
                  <img
                    src={selectedDevice.qr_code_url}
                    alt="Device QR Code"
                    style={{ maxWidth: '100%', height: 'auto', maxHeight: '300px' }}
                  />
                </Box>
              )}
              
              <Alert severity="info" sx={{ textAlign: 'left' }}>
                <Typography variant="body2">
                  <strong>Instructions:</strong>
                  <br />1. Print this QR code and attach it to the device
                  <br />2. Users can scan the QR code to instantly provision the device
                  <br />3. No manual configuration required - zero-config onboarding
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQrDialogOpen(false)}>Close</Button>
          <Button
            onClick={printQRCode}
            variant="contained"
            startIcon={<Print />}
          >
            Print QR Code
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProvisioningManagement;