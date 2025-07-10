// Health device presets for easy setup
export const healthDevicePresets = [
  {
    name: 'Apple Watch Series 9',
    description: 'Premium smartwatch with health monitoring',
    category: 'Fitness Tracker',
    manufacturer: 'Apple',
    model: 'Series 9',
    capabilities: [
      'heart_rate',
      'step_counting',
      'calorie_tracking',
      'sleep_tracking',
      'workout_tracking',
      'fall_detection',
      'emergency_alert'
    ],
    default_config: {
      sync_frequency: 'realtime',
      data_retention: '1_year',
      health_alerts: true
    }
  },
  {
    name: 'Fitbit Charge 5',
    description: 'Advanced fitness tracker with stress management',
    category: 'Fitness Tracker',
    manufacturer: 'Fitbit',
    model: 'Charge 5',
    capabilities: [
      'heart_rate',
      'step_counting',
      'sleep_tracking',
      'stress_monitoring',
      'calorie_tracking'
    ],
    default_config: {
      sync_frequency: 'hourly',
      data_retention: '2_years',
      health_alerts: true
    }
  },
  {
    name: 'Withings Body+',
    description: 'Smart scale with body composition analysis',
    category: 'Smart Scale',
    manufacturer: 'Withings',
    model: 'Body+',
    capabilities: [
      'weight_measurement',
      'body_fat',
      'muscle_mass',
      'bone_density'
    ],
    default_config: {
      sync_frequency: 'daily',
      data_retention: '5_years',
      health_alerts: false
    }
  },
  {
    name: 'Omron HeartGuide',
    description: 'Clinical-grade blood pressure monitor watch',
    category: 'Blood Pressure Monitor',
    manufacturer: 'Omron',
    model: 'HeartGuide',
    capabilities: [
      'blood_pressure',
      'heart_rate',
      'pulse_pressure'
    ],
    default_config: {
      sync_frequency: 'manual',
      data_retention: '10_years',
      health_alerts: true
    }
  },
  {
    name: 'Oura Ring Gen3',
    description: 'Advanced sleep and recovery tracking ring',
    category: 'Sleep Tracker',
    manufacturer: 'Oura',
    model: 'Generation 3',
    capabilities: [
      'sleep_tracking',
      'heart_rate_variability',
      'body_temperature',
      'stress_monitoring'
    ],
    default_config: {
      sync_frequency: 'daily',
      data_retention: '2_years',
      health_alerts: true
    }
  },
  {
    name: 'Dyson Pure Cool',
    description: 'Air purifier with quality monitoring',
    category: 'Air Quality Monitor',
    manufacturer: 'Dyson',
    model: 'Pure Cool',
    capabilities: [
      'air_quality',
      'temperature',
      'humidity',
      'voc_levels'
    ],
    default_config: {
      sync_frequency: 'realtime',
      data_retention: '1_year',
      health_alerts: true
    }
  },
  {
    name: 'Garmin Venu 2',
    description: 'GPS smartwatch with health monitoring',
    category: 'Fitness Tracker',
    manufacturer: 'Garmin',
    model: 'Venu 2',
    capabilities: [
      'heart_rate',
      'step_counting',
      'sleep_tracking',
      'workout_tracking',
      'stress_monitoring',
      'hydration_tracking'
    ],
    default_config: {
      sync_frequency: 'hourly',
      data_retention: '2_years',
      health_alerts: true
    }
  },
  {
    name: 'Beurer BM 67',
    description: 'Bluetooth blood pressure monitor',
    category: 'Blood Pressure Monitor',
    manufacturer: 'Beurer',
    model: 'BM 67',
    capabilities: [
      'blood_pressure',
      'heart_rate'
    ],
    default_config: {
      sync_frequency: 'manual',
      data_retention: '5_years',
      health_alerts: true
    }
  }
];

export const getHealthDevicePreset = (brand, model) => {
  return healthDevicePresets.find(preset => 
    preset.manufacturer.toLowerCase() === brand.toLowerCase() && 
    preset.model.toLowerCase().includes(model.toLowerCase())
  );
};

export const getHealthDevicesByCategory = (category) => {
  return healthDevicePresets.filter(preset => preset.category === category);
};

export default healthDevicePresets;