import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

const LoadingScreen: React.FC = () => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="primary.main"
      color="white"
    >
      <CircularProgress size={64} color="inherit" sx={{ mb: 2 }} />
      <Typography variant="h5" gutterBottom>
        Station Traffeyère IoT/AI Platform
      </Typography>
      <Typography variant="body2" sx={{ opacity: 0.8 }}>
        RNCP 39394 - Expert en Systèmes d'Information et Sécurité
      </Typography>
    </Box>
  );
};

export default LoadingScreen;