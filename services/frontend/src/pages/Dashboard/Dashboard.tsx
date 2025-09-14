import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { 
  Dashboard as DashboardIcon, 
  Sensors as SensorsIcon,
  Speed as SpeedIcon,
  Analytics as AnalyticsIcon 
} from '@mui/icons-material';

const Dashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Dashboard Principal
      </Typography>
      
      <Grid container spacing={3}>
        {/* Station Status */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <DashboardIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Statut Station</Typography>
              </Box>
              <Chip 
                label="Opérationnelle" 
                color="success" 
                size="small"
                sx={{ mb: 1 }}
              />
              <Typography variant="body2" color="text.secondary">
                Tous les systèmes fonctionnent normalement
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Capteurs IoT */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SensorsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Capteurs IoT</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                8/8
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Capteurs actifs
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <SpeedIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Performance IA</Typography>
              </Box>
              <Typography variant="h4" color="success.main">
                97.6%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Précision détection anomalies
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Analyse */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <AnalyticsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Latence Edge AI</Typography>
              </Box>
              <Typography variant="h4" color="info.main">
                0.28ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Objectif &lt;1ms atteint
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Informations du projet */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Station Traffeyère IoT/AI Platform
              </Typography>
              <Typography variant="body1" paragraph>
                Plateforme IoT/IA convergente pour la transformation digitale des infrastructures 
                critiques de traitement des eaux. Architecture Edge Computing + 5G-TSN + Digital Twin + Blockchain.
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                <Chip label="RNCP 39394" color="primary" />
                <Chip label="Edge AI" color="info" />
                <Chip label="Digital Twin" color="secondary" />
                <Chip label="IoT Platform" color="success" />
                <Chip label="Cybersécurité" color="warning" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;