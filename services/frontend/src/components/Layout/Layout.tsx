/**
 * =============================================================================
 * LAYOUT COMPONENT - Station Traffeyère IoT/AI Platform
 * Layout principal avec navigation - RNCP 39394
 * =============================================================================
 */

import React from 'react';
import { Box, Container, Typography, AppBar, Toolbar } from '@mui/material';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Header */}
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Station Traffeyère IoT/AI Platform
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            RNCP 39394
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, py: 3, backgroundColor: '#f5f5f5' }}>
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 2,
          px: 2,
          backgroundColor: '#1976d2',
          color: 'white',
          textAlign: 'center',
        }}
      >
        <Typography variant="body2">
          Station Traffeyère IoT/AI Platform © 2025 - Expert en Systèmes d'Information et Sécurité
        </Typography>
      </Box>
    </Box>
  );
};

export default Layout;