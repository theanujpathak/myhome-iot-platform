import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import { toast } from 'react-toastify';

const DeviceContext = createContext();

export const useDevices = () => {
  const context = useContext(DeviceContext);
  if (!context) {
    throw new Error('useDevices must be used within a DeviceProvider');
  }
  return context;
};

export const DeviceProvider = ({ children }) => {
  const { authenticated } = useAuth();
  const [devices, setDevices] = useState([]);
  const [locations, setLocations] = useState([]);
  const [deviceTypes, setDeviceTypes] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (authenticated) {
      // Add a small delay to ensure token is properly set
      setTimeout(() => {
        fetchDevices();
        fetchLocations();
        fetchDeviceTypes();
      }, 100);
    }
  }, [authenticated]);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:3002/api/devices');
      setDevices(response.data);
    } catch (error) {
      console.error('Failed to fetch devices:', error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        // Token issue - let axios interceptor handle it
        console.log('Authentication error, will retry with refreshed token');
      } else {
        toast.error('Failed to fetch devices');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get('http://localhost:3002/api/locations');
      setLocations(response.data);
    } catch (error) {
      console.error('Failed to fetch locations:', error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('Authentication error, will retry with refreshed token');
      } else {
        toast.error('Failed to fetch locations');
      }
    }
  };

  const fetchDeviceTypes = async () => {
    try {
      const response = await axios.get('http://localhost:3002/api/device-types');
      setDeviceTypes(response.data);
    } catch (error) {
      console.error('Failed to fetch device types:', error);
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('Authentication error, will retry with refreshed token');
      } else {
        toast.error('Failed to fetch device types');
      }
    }
  };

  const createDevice = async (deviceData) => {
    try {
      const response = await axios.post('http://localhost:3002/api/devices', deviceData);
      setDevices([...devices, response.data]);
      toast.success('Device created successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to create device:', error);
      toast.error('Failed to create device');
      throw error;
    }
  };

  const updateDevice = async (deviceId, deviceData) => {
    try {
      const response = await axios.put(`http://localhost:3002/api/devices/${deviceId}`, deviceData);
      setDevices(devices.map(device => 
        device.id === deviceId ? response.data : device
      ));
      toast.success('Device updated successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to update device:', error);
      toast.error('Failed to update device');
      throw error;
    }
  };

  const deleteDevice = async (deviceId) => {
    try {
      await axios.delete(`http://localhost:3002/api/devices/${deviceId}`);
      setDevices(devices.filter(device => device.id !== deviceId));
      toast.success('Device deleted successfully');
    } catch (error) {
      console.error('Failed to delete device:', error);
      toast.error('Failed to delete device');
      throw error;
    }
  };

  const sendDeviceCommand = async (deviceId, command, parameters = {}) => {
    try {
      const response = await axios.post(`http://localhost:3002/api/devices/${deviceId}/command`, {
        command,
        parameters
      });
      toast.success('Command sent successfully');
      
      // Refresh device data to get updated status
      await fetchDevices();
      
      return response.data;
    } catch (error) {
      console.error('Failed to send device command:', error);
      toast.error('Failed to send command');
      throw error;
    }
  };

  const createLocation = async (locationData) => {
    try {
      const response = await axios.post('http://localhost:3002/api/locations', locationData);
      setLocations([...locations, response.data]);
      toast.success('Location created successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to create location:', error);
      toast.error('Failed to create location');
      throw error;
    }
  };

  const updateLocation = async (locationId, locationData) => {
    try {
      const response = await axios.put(`http://localhost:3002/api/locations/${locationId}`, locationData);
      setLocations(locations.map(location => 
        location.id === locationId ? response.data : location
      ));
      toast.success('Location updated successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to update location:', error);
      toast.error('Failed to update location');
      throw error;
    }
  };

  const deleteLocation = async (locationId) => {
    try {
      await axios.delete(`http://localhost:3002/api/locations/${locationId}`);
      setLocations(locations.filter(location => location.id !== locationId));
      toast.success('Location deleted successfully');
    } catch (error) {
      console.error('Failed to delete location:', error);
      toast.error('Failed to delete location');
      throw error;
    }
  };

  const getDevicesByLocation = (locationId) => {
    if (!locationId) return devices.filter(device => !device.location_id);
    return devices.filter(device => device.location_id === locationId);
  };

  const getOnlineDevices = () => {
    return devices.filter(device => device.is_online);
  };

  const getOfflineDevices = () => {
    return devices.filter(device => !device.is_online);
  };

  const getDevicesByType = (deviceTypeId) => {
    return devices.filter(device => device.device_type_id === deviceTypeId);
  };

  const createDeviceType = async (deviceTypeData) => {
    try {
      const response = await axios.post('http://localhost:3002/api/device-types', deviceTypeData);
      setDeviceTypes([...deviceTypes, response.data]);
      toast.success('Device type created successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to create device type:', error);
      toast.error('Failed to create device type');
      throw error;
    }
  };

  const value = {
    devices,
    locations,
    deviceTypes,
    loading,
    fetchDevices,
    fetchLocations,
    fetchDeviceTypes,
    createDevice,
    updateDevice,
    deleteDevice,
    sendDeviceCommand,
    createLocation,
    updateLocation,
    deleteLocation,
    createDeviceType,
    getDevicesByLocation,
    getOnlineDevices,
    getOfflineDevices,
    getDevicesByType,
  };

  return (
    <DeviceContext.Provider value={value}>
      {children}
    </DeviceContext.Provider>
  );
};