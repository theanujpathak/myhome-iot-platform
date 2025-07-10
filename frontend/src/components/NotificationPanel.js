import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Button,
  Divider,
  Chip,
  Avatar,
  Alert
} from '@mui/material';
import {
  Close,
  Warning,
  CheckCircle,
  Info,
  Error,
  Notifications,
  DevicesOther,
  Delete,
  MarkEmailRead
} from '@mui/icons-material';
import { useNotifications } from '../contexts/NotificationContext';

const NotificationPanel = ({ open, onClose }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, dismissNotification } = useNotifications();

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle color="success" />;
      case 'warning':
        return <Warning color="warning" />;
      case 'error':
        return <Error color="error" />;
      case 'info':
      default:
        return <Info color="info" />;
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'success':
        return 'success.light';
      case 'warning':
        return 'warning.light';
      case 'error':
        return 'error.light';
      case 'info':
      default:
        return 'info.light';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
  };

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { width: 400, maxWidth: '90vw' }
      }}
    >
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Notifications />
            <Typography variant="h6">
              Notifications
            </Typography>
            {unreadCount > 0 && (
              <Chip 
                label={unreadCount} 
                color="primary" 
                size="small"
              />
            )}
          </Box>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>

        {notifications.length > 0 && unreadCount > 0 && (
          <Box sx={{ mb: 2 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={markAllAsRead}
              startIcon={<MarkEmailRead />}
              fullWidth
            >
              Mark All as Read
            </Button>
          </Box>
        )}

        <Divider />

        {notifications.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <DevicesOther sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No notifications
            </Typography>
            <Typography variant="body2" color="text.secondary">
              You're all caught up! New notifications will appear here.
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {notifications.map((notification, index) => (
              <React.Fragment key={notification.id}>
                <ListItem
                  sx={{
                    bgcolor: notification.read ? 'transparent' : 'action.hover',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'action.selected'
                    }
                  }}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <ListItemIcon>
                    <Avatar
                      sx={{ 
                        bgcolor: getNotificationColor(notification.type),
                        width: 32,
                        height: 32
                      }}
                    >
                      {getNotificationIcon(notification.type)}
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Typography
                          variant="subtitle2"
                          sx={{ 
                            fontWeight: notification.read ? 'normal' : 'bold',
                            lineHeight: 1.2
                          }}
                        >
                          {notification.title}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {formatTimestamp(notification.timestamp)}
                          </Typography>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              dismissNotification(notification.id);
                            }}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Box>
                      </Box>
                    }
                    secondary={
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mt: 0.5 }}
                      >
                        {notification.message}
                      </Typography>
                    }
                  />
                </ListItem>
                {index < notifications.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}

        {notifications.length > 0 && (
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
            <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
              Notifications are generated based on your device status and system activities.
            </Alert>
          </Box>
        )}
      </Box>
    </Drawer>
  );
};

export default NotificationPanel;