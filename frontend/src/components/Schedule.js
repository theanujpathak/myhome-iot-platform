import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  IconButton
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  Add,
  Edit,
  Delete,
  PlayArrow,
  Pause,
  AccessTime,
  Devices
} from '@mui/icons-material';

const Schedule = () => {
  const [schedules] = useState([
    {
      id: 1,
      name: 'Morning Lights',
      description: 'Turn on living room lights at 7 AM',
      trigger: 'time',
      time: '07:00',
      days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
      actions: [
        { device: 'Living Room Light', action: 'Turn On', brightness: 80 }
      ],
      enabled: true,
      next_run: '2024-01-15T07:00:00Z'
    },
    {
      id: 2,
      name: 'Goodnight Routine',
      description: 'Turn off all lights and lock doors at 11 PM',
      trigger: 'time',
      time: '23:00',
      days: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      actions: [
        { device: 'All Lights', action: 'Turn Off' },
        { device: 'Front Door Lock', action: 'Lock' }
      ],
      enabled: true,
      next_run: '2024-01-14T23:00:00Z'
    },
    {
      id: 3,
      name: 'Weekend Wake Up',
      description: 'Gradual lighting for weekend mornings',
      trigger: 'time',
      time: '08:30',
      days: ['Sat', 'Sun'],
      actions: [
        { device: 'Bedroom Light', action: 'Gradual On', duration: '30 minutes' }
      ],
      enabled: false,
      next_run: '2024-01-20T08:30:00Z'
    }
  ]);

  const formatTime = (time) => {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatNextRun = (datetime) => {
    return new Date(datetime).toLocaleDateString() + ' at ' + 
           new Date(datetime).toLocaleTimeString([], { 
             hour: '2-digit', 
             minute: '2-digit' 
           });
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Schedules & Automation
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => console.log('Add schedule')}
        >
          Add Schedule
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Schedule management is coming soon! Create automated routines to control your devices based on time, 
        device states, or environmental conditions.
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Typography variant="h6" gutterBottom>
            Active Schedules
          </Typography>
          {schedules.map((schedule) => (
            <Card key={schedule.id} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="h6" component="h3">
                      {schedule.name}
                    </Typography>
                    <Typography color="text.secondary" gutterBottom>
                      {schedule.description}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label={schedule.enabled ? 'Enabled' : 'Disabled'}
                      color={schedule.enabled ? 'success' : 'default'}
                      size="small"
                    />
                    <IconButton size="small" onClick={() => console.log('Edit', schedule.id)}>
                      <Edit />
                    </IconButton>
                    <IconButton size="small" onClick={() => console.log('Delete', schedule.id)}>
                      <Delete />
                    </IconButton>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <AccessTime sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'text-bottom' }} />
                    {formatTime(schedule.time)} on {schedule.days.join(', ')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Next run: {formatNextRun(schedule.next_run)}
                  </Typography>
                </Box>

                <Typography variant="body2" sx={{ mb: 1, fontWeight: 'medium' }}>
                  Actions:
                </Typography>
                <List dense>
                  {schedule.actions.map((action, index) => (
                    <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <Devices sx={{ fontSize: 20 }} />
                      </ListItemIcon>
                      <ListItemText
                        primary={`${action.device}: ${action.action}`}
                        secondary={action.brightness ? `Brightness: ${action.brightness}%` : action.duration}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          ))}
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Schedule Types
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <AccessTime />
                  </ListItemIcon>
                  <ListItemText
                    primary="Time-based"
                    secondary="Run at specific times and days"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Devices />
                  </ListItemIcon>
                  <ListItemText
                    primary="Device Triggered"
                    secondary="React to device state changes"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <ScheduleIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary="Conditional"
                    secondary="Based on multiple conditions"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<PlayArrow />}
                  onClick={() => console.log('Run all schedules')}
                >
                  Run All Schedules
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Pause />}
                  onClick={() => console.log('Pause all schedules')}
                >
                  Pause All Schedules
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Statistics
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Total Schedules:</Typography>
                <Typography variant="body2" fontWeight="bold">{schedules.length}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Active:</Typography>
                <Typography variant="body2" fontWeight="bold" color="success.main">
                  {schedules.filter(s => s.enabled).length}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2">Disabled:</Typography>
                <Typography variant="body2" fontWeight="bold" color="text.secondary">
                  {schedules.filter(s => !s.enabled).length}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Schedule;