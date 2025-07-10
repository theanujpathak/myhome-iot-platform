import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Box,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Badge,
  Alert,
  Snackbar,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Upload,
  CloudUpload,
  GetApp,
  Security,
  Build,
  Timeline,
  Devices,
  Warning,
  CheckCircle,
  Error,
  Info,
  Refresh,
  PlayArrow,
  Pause,
  Stop,
  Settings,
  Assessment
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4]
  }
}));

const StatusChip = styled(Chip)(({ theme, status }) => ({
  fontWeight: 'bold',
  ...(status === 'stable' && {
    backgroundColor: theme.palette.success.main,
    color: theme.palette.success.contrastText
  }),
  ...(status === 'testing' && {
    backgroundColor: theme.palette.warning.main,
    color: theme.palette.warning.contrastText
  }),
  ...(status === 'development' && {
    backgroundColor: theme.palette.info.main,
    color: theme.palette.info.contrastText
  }),
  ...(status === 'deprecated' && {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText
  })
}));

const FirmwareManagement = () => {
  const { authenticated } = useAuth();
  const [currentTab, setCurrentTab] = useState(0);
  const [firmwares, setFirmwares] = useState([]);
  const [rollouts, setRollouts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [rolloutDialog, setRolloutDialog] = useState(false);
  const [selectedFirmware, setSelectedFirmware] = useState(null);
  const [stats, setStats] = useState({});
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    deviceType: '',
    boardModel: '',
    version: '',
    status: 'development',
    description: '',
    changelog: '',
    file: null
  });

  // Rollout form state
  const [rolloutForm, setRolloutForm] = useState({
    firmwareId: '',
    name: '',
    description: '',
    strategy: 'manual',
    targetDevices: [],
    targetDeviceTypes: [],
    gradualPercentage: 10,
    maxConcurrentUpdates: 5
  });

  useEffect(() => {
    if (authenticated) {
      fetchData();
    }
  }, [authenticated, currentTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const promises = [
        fetchFirmwares(),
        fetchStats()
      ];

      if (currentTab === 1) {
        promises.push(fetchRollouts());
      }

      if (currentTab === 2) {
        promises.push(fetchDevices());
      }

      await Promise.all(promises);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      showNotification('Failed to fetch data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchFirmwares = async () => {
    try {
      const response = await axios.get('http://localhost:3004/api/firmware');
      setFirmwares(response.data);
    } catch (error) {
      console.error('Failed to fetch firmwares:', error);
    }
  };

  const fetchRollouts = async () => {
    try {
      const response = await axios.get('http://localhost:3004/api/rollouts');
      setRollouts(response.data);
    } catch (error) {
      console.error('Failed to fetch rollouts:', error);
    }
  };

  const fetchDevices = async () => {
    try {
      const response = await axios.get('http://localhost:3002/api/devices');
      setDevices(response.data);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:3004/api/stats/firmware');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleUpload = async () => {
    if (!uploadForm.file) {
      showNotification('Please select a firmware file', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('firmware_file', uploadForm.file);
    formData.append('device_type', uploadForm.deviceType);
    formData.append('board_model', uploadForm.boardModel);
    formData.append('version', uploadForm.version);
    formData.append('status', uploadForm.status);
    formData.append('description', uploadForm.description);
    formData.append('changelog', uploadForm.changelog);

    try {
      await axios.post('http://localhost:3004/api/firmware/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      showNotification('Firmware uploaded successfully', 'success');
      setUploadDialog(false);
      setUploadForm({
        deviceType: '',
        boardModel: '',
        version: '',
        status: 'development',
        description: '',
        changelog: '',
        file: null
      });
      fetchFirmwares();
    } catch (error) {
      console.error('Upload failed:', error);
      showNotification('Upload failed: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const handleCreateRollout = async () => {
    try {
      await axios.post('http://localhost:3004/api/rollouts', rolloutForm);
      showNotification('Rollout created successfully', 'success');
      setRolloutDialog(false);
      setRolloutForm({
        firmwareId: '',
        name: '',
        description: '',
        strategy: 'manual',
        targetDevices: [],
        targetDeviceTypes: [],
        gradualPercentage: 10,
        maxConcurrentUpdates: 5
      });
      fetchRollouts();
    } catch (error) {
      console.error('Rollout creation failed:', error);
      showNotification('Rollout creation failed: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const handleApproveFirmware = async (firmwareId) => {
    try {
      await axios.post(`http://localhost:3004/api/firmware/${firmwareId}/approve`);
      showNotification('Firmware approved successfully', 'success');
      fetchFirmwares();
    } catch (error) {
      console.error('Approval failed:', error);
      showNotification('Approval failed: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const handleStartRollout = async (rolloutId) => {
    try {
      await axios.post(`http://localhost:3004/api/rollouts/${rolloutId}/start`);
      showNotification('Rollout started successfully', 'success');
      fetchRollouts();
    } catch (error) {
      console.error('Failed to start rollout:', error);
      showNotification('Failed to start rollout: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const handleUpdateDevice = async (deviceId, firmwareId) => {
    try {
      await axios.post(`http://localhost:3004/api/devices/${deviceId}/update`, {
        firmware_id: firmwareId,
        force_update: false
      });
      showNotification('Device update initiated', 'success');
    } catch (error) {
      console.error('Device update failed:', error);
      showNotification('Device update failed: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({ open: true, message, severity });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'stable':
        return <CheckCircle color="success" />;
      case 'testing':
        return <Warning color="warning" />;
      case 'development':
        return <Info color="info" />;
      case 'deprecated':
        return <Error color="error" />;
      default:
        return <Info />;
    }
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'info';
    }
  };

  const renderFirmwaresList = () => (
    <Grid container spacing={3}>
      {firmwares.map((firmware) => (
        <Grid item xs={12} md={6} lg={4} key={firmware.id}>
          <StyledCard>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" component="div">
                  {firmware.device_type}
                </Typography>
                <StatusChip
                  status={firmware.status}
                  label={firmware.status}
                  size="small"
                  icon={getStatusIcon(firmware.status)}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {firmware.board_model} - v{firmware.version}
              </Typography>
              
              <Typography variant="body2" gutterBottom>
                {firmware.description || 'No description available'}
              </Typography>
              
              <Box mt={2}>
                <Typography variant="caption" display="block">
                  Size: {(firmware.file_size / 1024).toFixed(1)} KB
                </Typography>
                <Typography variant="caption" display="block">
                  Built: {new Date(firmware.build_date).toLocaleDateString()}
                </Typography>
                <Typography variant="caption" display="block">
                  Created by: {firmware.created_by}
                </Typography>
              </Box>
              
              {firmware.breaking_changes && firmware.breaking_changes.length > 0 && (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  Contains breaking changes
                </Alert>
              )}
              
              {firmware.security_fixes && firmware.security_fixes.length > 0 && (
                <Alert severity="info" sx={{ mt: 1 }}>
                  Includes security fixes
                </Alert>
              )}
            </CardContent>
            
            <CardActions>
              <Button
                size="small"
                startIcon={<GetApp />}
                onClick={() => window.open(firmware.download_url, '_blank')}
              >
                Download
              </Button>
              
              {firmware.status === 'development' && (
                <Button
                  size="small"
                  startIcon={<Security />}
                  onClick={() => handleApproveFirmware(firmware.id)}
                  color="primary"
                >
                  Approve
                </Button>
              )}
              
              <Button
                size="small"
                startIcon={<Devices />}
                onClick={() => {
                  setSelectedFirmware(firmware);
                  setRolloutForm({ ...rolloutForm, firmwareId: firmware.id });
                  setRolloutDialog(true);
                }}
              >
                Deploy
              </Button>
            </CardActions>
          </StyledCard>
        </Grid>
      ))}
    </Grid>
  );

  const renderRolloutsList = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Firmware</TableCell>
            <TableCell>Strategy</TableCell>
            <TableCell>Progress</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rollouts.map((rollout) => (
            <TableRow key={rollout.id}>
              <TableCell>{rollout.name}</TableCell>
              <TableCell>{rollout.firmware_id}</TableCell>
              <TableCell>
                <Chip label={rollout.strategy} size="small" />
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={(rollout.successful_updates / rollout.total_devices) * 100}
                    />
                  </Box>
                  <Box sx={{ minWidth: 35 }}>
                    <Typography variant="body2" color="text.secondary">
                      {rollout.successful_updates}/{rollout.total_devices}
                    </Typography>
                  </Box>
                </Box>
              </TableCell>
              <TableCell>
                <StatusChip
                  status={rollout.status}
                  label={rollout.status}
                  size="small"
                />
              </TableCell>
              <TableCell>
                {rollout.status === 'pending' && (
                  <Button
                    size="small"
                    startIcon={<PlayArrow />}
                    onClick={() => handleStartRollout(rollout.id)}
                  >
                    Start
                  </Button>
                )}
                {rollout.status === 'active' && (
                  <Button
                    size="small"
                    startIcon={<Pause />}
                    onClick={() => {/* Handle pause */}}
                  >
                    Pause
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderDevicesList = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Device</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Current Version</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {devices.map((device) => (
            <TableRow key={device.id}>
              <TableCell>{device.name}</TableCell>
              <TableCell>{device.device_type?.name || 'Unknown'}</TableCell>
              <TableCell>{device.firmware_version || 'Unknown'}</TableCell>
              <TableCell>
                <Chip
                  label={device.is_online ? 'Online' : 'Offline'}
                  size="small"
                  color={device.is_online ? 'success' : 'error'}
                />
              </TableCell>
              <TableCell>
                <Button
                  size="small"
                  startIcon={<Build />}
                  onClick={() => {
                    // Show firmware selection dialog
                  }}
                  disabled={!device.is_online}
                >
                  Update
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );

  const renderStats = () => (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h4" component="div">
              {stats.total_firmwares || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Firmwares
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h4" component="div">
              {stats.recent_uploads || 0}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Recent Uploads
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h4" component="div">
              {((stats.total_size || 0) / 1024 / 1024).toFixed(1)} MB
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Size
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={3}>
        <Card>
          <CardContent>
            <Typography variant="h4" component="div">
              {Object.keys(stats.by_device_type || {}).length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Device Types
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Firmware Management
      </Typography>

      {renderStats()}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
          <Tab label="Firmwares" />
          <Tab label="Rollouts" />
          <Tab label="Devices" />
        </Tabs>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={fetchData}
          disabled={loading}
        >
          Refresh
        </Button>
        
        <Box>
          {currentTab === 0 && (
            <Button
              variant="contained"
              startIcon={<CloudUpload />}
              onClick={() => setUploadDialog(true)}
            >
              Upload Firmware
            </Button>
          )}
          {currentTab === 1 && (
            <Button
              variant="contained"
              startIcon={<Timeline />}
              onClick={() => setRolloutDialog(true)}
            >
              Create Rollout
            </Button>
          )}
        </Box>
      </Box>

      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {currentTab === 0 && renderFirmwaresList()}
          {currentTab === 1 && renderRolloutsList()}
          {currentTab === 2 && renderDevicesList()}
        </>
      )}

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Firmware</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Device Type</InputLabel>
                <Select
                  value={uploadForm.deviceType}
                  onChange={(e) => setUploadForm({ ...uploadForm, deviceType: e.target.value })}
                >
                  <MenuItem value="ESP32">ESP32</MenuItem>
                  <MenuItem value="ESP8266">ESP8266</MenuItem>
                  <MenuItem value="Arduino Uno">Arduino Uno</MenuItem>
                  <MenuItem value="STM32">STM32</MenuItem>
                  <MenuItem value="Raspberry Pi Pico">Raspberry Pi Pico</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Board Model"
                value={uploadForm.boardModel}
                onChange={(e) => setUploadForm({ ...uploadForm, boardModel: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Version"
                value={uploadForm.version}
                onChange={(e) => setUploadForm({ ...uploadForm, version: e.target.value })}
                placeholder="1.0.0"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={uploadForm.status}
                  onChange={(e) => setUploadForm({ ...uploadForm, status: e.target.value })}
                >
                  <MenuItem value="development">Development</MenuItem>
                  <MenuItem value="testing">Testing</MenuItem>
                  <MenuItem value="stable">Stable</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={uploadForm.description}
                onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Changelog"
                value={uploadForm.changelog}
                onChange={(e) => setUploadForm({ ...uploadForm, changelog: e.target.value })}
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12}>
              <input
                accept=".bin,.hex,.uf2"
                style={{ display: 'none' }}
                id="firmware-file"
                type="file"
                onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files[0] })}
              />
              <label htmlFor="firmware-file">
                <Button variant="outlined" component="span" startIcon={<Upload />} fullWidth>
                  {uploadForm.file ? uploadForm.file.name : 'Select Firmware File'}
                </Button>
              </label>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>Cancel</Button>
          <Button onClick={handleUpload} variant="contained">Upload</Button>
        </DialogActions>
      </Dialog>

      {/* Rollout Dialog */}
      <Dialog open={rolloutDialog} onClose={() => setRolloutDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Rollout</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Rollout Name"
                value={rolloutForm.name}
                onChange={(e) => setRolloutForm({ ...rolloutForm, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={rolloutForm.description}
                onChange={(e) => setRolloutForm({ ...rolloutForm, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Strategy</InputLabel>
                <Select
                  value={rolloutForm.strategy}
                  onChange={(e) => setRolloutForm({ ...rolloutForm, strategy: e.target.value })}
                >
                  <MenuItem value="immediate">Immediate</MenuItem>
                  <MenuItem value="gradual">Gradual</MenuItem>
                  <MenuItem value="scheduled">Scheduled</MenuItem>
                  <MenuItem value="manual">Manual</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Max Concurrent Updates"
                type="number"
                value={rolloutForm.maxConcurrentUpdates}
                onChange={(e) => setRolloutForm({ ...rolloutForm, maxConcurrentUpdates: parseInt(e.target.value) })}
              />
            </Grid>
            {rolloutForm.strategy === 'gradual' && (
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Gradual Percentage"
                  type="number"
                  value={rolloutForm.gradualPercentage}
                  onChange={(e) => setRolloutForm({ ...rolloutForm, gradualPercentage: parseInt(e.target.value) })}
                  inputProps={{ min: 1, max: 100 }}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRolloutDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateRollout} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert
          onClose={() => setNotification({ ...notification, open: false })}
          severity={notification.severity}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default FirmwareManagement;