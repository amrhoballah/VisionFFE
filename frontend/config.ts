// Configuration for the frontend application

export const config = {
  // Backend API configuration
  api: {
    baseUrl: process.env.NODE_ENV === 'production' 
      ? process.env.REACT_APP_API_URL || 'https://amrhoballah--vision-ffe-api-fast-app.modal.run'  // Replace with your Modal URL
      : 'http://localhost:8080',
  },
  
  // Feature flags
  features: {
    enableRegistration: true,
    enablePasswordReset: false,
    enableEmailVerification: false,
  },
  
  // UI configuration
  ui: {
    appName: 'VisionFFE',
    maxFileSize: 10 * 1024 * 1024, // 10MB
    supportedImageTypes: ['image/jpeg', 'image/png', 'image/webp'],
  },
};

export default config;
