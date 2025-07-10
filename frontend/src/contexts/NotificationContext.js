import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { useDevices } from './DeviceContext';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const { user } = useAuth();
  const { devices } = useDevices();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Generate notifications based on system state
  useEffect(() => {
    if (!devices || devices.length === 0) return;

    const newNotifications = [];
    let id = 1;

    // Check for offline devices
    const offlineDevices = devices.filter(device => !device.is_online);
    offlineDevices.forEach(device => {
      newNotifications.push({
        id: id++,
        type: 'warning',
        title: 'Device Offline',
        message: `${device.name} is currently offline`,
        timestamp: new Date().toISOString(),
        read: false,
        deviceId: device.id
      });
    });

    // Check for recently added devices
    const recentDevices = devices.filter(device => {
      const createdAt = new Date(device.created_at);
      const hourAgo = new Date(Date.now() - 60 * 60 * 1000);
      return createdAt > hourAgo;
    });

    recentDevices.forEach(device => {
      newNotifications.push({
        id: id++,
        type: 'success',
        title: 'New Device Added',
        message: `${device.name} has been successfully added to your system`,
        timestamp: new Date().toISOString(),
        read: false,
        deviceId: device.id
      });
    });

    // Add system status notification
    if (devices.length > 0) {
      const onlineCount = devices.filter(device => device.is_online).length;
      const totalCount = devices.length;
      
      newNotifications.push({
        id: id++,
        type: 'info',
        title: 'System Status',
        message: `${onlineCount} of ${totalCount} devices are online`,
        timestamp: new Date().toISOString(),
        read: false
      });
    }

    // Add welcome notification for new users
    if (user && !localStorage.getItem('welcomeNotificationShown')) {
      newNotifications.push({
        id: id++,
        type: 'info',
        title: 'Welcome to Home Automation',
        message: `Welcome ${user.first_name || user.username}! Your smart home is ready.`,
        timestamp: new Date().toISOString(),
        read: false
      });
      localStorage.setItem('welcomeNotificationShown', 'true');
    }

    setNotifications(newNotifications);
    setUnreadCount(newNotifications.filter(n => !n.read).length);
  }, [devices, user]);

  const markAsRead = (notificationId) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === notificationId 
          ? { ...notification, read: true }
          : notification
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
    setUnreadCount(0);
  };

  const dismissNotification = (notificationId) => {
    setNotifications(prev => 
      prev.filter(notification => notification.id !== notificationId)
    );
    setUnreadCount(prev => {
      const notification = notifications.find(n => n.id === notificationId);
      return notification && !notification.read ? prev - 1 : prev;
    });
  };

  const addNotification = (notification) => {
    const newNotification = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      read: false,
      ...notification
    };
    setNotifications(prev => [newNotification, ...prev]);
    setUnreadCount(prev => prev + 1);
  };

  const value = {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    addNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};