import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  IconButton,
  Tooltip,
  LinearProgress,
  Alert,
  Badge,
  Fab,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Sensors,
  WaterDrop,
  Speed,
  Warning,
  CheckCircle,
  Error,
  Info,
  Refresh,
  Fullscreen,
  VoiceChat,
  SmartToy,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import dayjs from 'dayjs';

import { useIoTData } from '@hooks/useIoTData';
import { useWebSocket } from '@hooks/useWebSocket';
import IoTSensorGrid from './IoTSensorGrid';
import AlertsPanel from './AlertsPanel';
import MetricsOverview from './MetricsOverview';
import RealTimeChart from '@components/Charts/RealTimeChart';
import { IoTSensor, AlertLevel, SystemMetrics } from '@types/iot.types';

interface MainDashboardProps {
  onNavigateToXAI?: () => void;
  onNavigateToDigitalTwin?: () => void;
  onOpenVoiceAssistant?: () => void;
}

const MainDashboard: React.FC<MainDashboardProps> = ({
  onNavigateToXAI,
  onNavigateToDigitalTwin,
  onOpenVoiceAssistant,
}) => {
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');

  // Hooks personnalisés
  const { sensors, metrics, loading, error, refreshData } = useIoTData();
  const { 
    isConnected, 
    lastMessage, 
    connectionStatus 
  } = useWebSocket('ws://backend:8000/ws/iot-realtime');

  // Mise à jour automatique toutes les 5 secondes
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date());
      if (!loading) {
        refreshData();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [loading, refreshData]);

  // Calculs des statistiques temps réel
  const sensorStats = React.useMemo(() => {
    if (!sensors || sensors.length === 0) return null;

    const totalSensors = sensors.length;
    const onlineSensors = sensors.filter(s => s.status === 'online').length;
    const warningSensors = sensors.filter(s => s.alertLevel === 'warning').length;
    const criticalSensors = sensors.filter(s => s.alertLevel === 'critical').length;
    const anomalies = sensors.filter(s => s.hasAnomaly).length;

    return {
      total: totalSensors,
      online: onlineSensors,
      offline: totalSensors - onlineSensors,
      warning: warningSensors,
      critical: criticalSensors,
      anomalies,
      healthPercentage: Math.round((onlineSensors / totalSensors) * 100),
    };
  }, [sensors]);

  const handleFullscreenToggle = () => {
    if (isFullscreen) {
      document.exitFullscreen?.();
    } else {
      document.documentElement.requestFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  };

  if (loading && !sensors) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>
          Chargement des données IoT...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        action={
          <Button color="inherit" size="small" onClick={refreshData}>
            Réessayer
          </Button>
        }
      >
        Erreur lors du chargement des données: {error.message}
      </Alert>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header avec statut système */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <DashboardIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" component="h1" fontWeight="bold">
                Station Traffeyère - Monitoring IoT/AI
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                <Chip
                  icon={isConnected ? <CheckCircle /> : <Error />}
                  label={isConnected ? 'Temps Réel' : 'Déconnecté'}
                  color={isConnected ? 'success' : 'error'}
                  size="small"
                />
                <Typography variant="body2" color="text.secondary">
                  Dernière mise à jour: {dayjs(lastUpdate).format('HH:mm:ss')}
                </Typography>
                {sensorStats && (
                  <Typography variant="body2" color="text.secondary">
                    {sensorStats.total} capteurs • {sensorStats.online} en ligne
                  </Typography>
                )}
              </Box>
            </Box>
          </Box>

          {/* Actions rapides */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Actualiser">
              <IconButton onClick={refreshData} disabled={loading}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="Plein écran">
              <IconButton onClick={handleFullscreenToggle}>
                <Fullscreen />
              </IconButton>
            </Tooltip>
            <Button
              variant="outlined"
              startIcon={<SmartToy />}
              onClick={onNavigateToXAI}
              sx={{ ml: 1 }}
            >
              IA Explicable
            </Button>
            <Button
              variant="outlined"
              startIcon={<DashboardIcon />}
              onClick={onNavigateToDigitalTwin}
              sx={{ ml: 1 }}
            >
              Digital Twin
            </Button>
          </Box>
        </Box>
      </motion.div>

      {/* Indicateurs de santé système */}
      {sensorStats && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                <CardContent sx={{ color: 'white' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h3" fontWeight="bold">
                        {sensorStats.total}
                      </Typography>
                      <Typography variant="body1">
                        Capteurs IoT
                      </Typography>
                    </Box>
                    <Sensors sx={{ fontSize: 48, opacity: 0.7 }} />
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={100} 
                    sx={{ 
                      mt: 2, 
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '& .MuiLinearProgress-bar': { bgcolor: 'rgba(255,255,255,0.8)' }
                    }} 
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                <CardContent sx={{ color: 'white' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h3" fontWeight="bold">
                        {sensorStats.healthPercentage}%
                      </Typography>
                      <Typography variant="body1">
                        Santé Système
                      </Typography>
                    </Box>
                    <Speed sx={{ fontSize: 48, opacity: 0.7 }} />
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={sensorStats.healthPercentage} 
                    sx={{ 
                      mt: 2, 
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '& .MuiLinearProgress-bar': { bgcolor: 'rgba(255,255,255,0.8)' }
                    }} 
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card sx={{ height: '100%', background: sensorStats.anomalies > 0 ? 'linear-gradient(135deg, #ff9a56 0%, #ff6b6b 100%)' : 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                <CardContent sx={{ color: 'white' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h3" fontWeight="bold">
                        {sensorStats.anomalies}
                      </Typography>
                      <Typography variant="body1">
                        Anomalies Détectées
                      </Typography>
                    </Box>
                    {sensorStats.anomalies > 0 ? 
                      <Warning sx={{ fontSize: 48, opacity: 0.7 }} /> : 
                      <CheckCircle sx={{ fontSize: 48, opacity: 0.7 }} />
                    }
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={sensorStats.anomalies > 0 ? (sensorStats.anomalies / sensorStats.total * 100) : 100} 
                    sx={{ 
                      mt: 2, 
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '& .MuiLinearProgress-bar': { bgcolor: 'rgba(255,255,255,0.8)' }
                    }} 
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={3}>
              <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h3" fontWeight="bold" color="text.primary">
                        {metrics?.edgeAI?.averageLatency || '0.28'}ms
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        Latence IA Edge
                      </Typography>
                    </Box>
                    <SmartToy sx={{ fontSize: 48, color: 'primary.main', opacity: 0.7 }} />
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                    P95 < 0.28ms (Objectif RNCP)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </motion.div>
      )}

      {/* Contenu principal */}
      <Grid container spacing={3}>
        {/* Grille des capteurs IoT */}
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <Paper sx={{ p: 2, height: '600px' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="medium">
                  Capteurs IoT Temps Réel
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {(['1h', '6h', '24h', '7d'] as const).map((range) => (
                    <Button
                      key={range}
                      size="small"
                      variant={selectedTimeRange === range ? 'contained' : 'outlined'}
                      onClick={() => setSelectedTimeRange(range)}
                    >
                      {range}
                    </Button>
                  ))}
                </Box>
              </Box>
              <IoTSensorGrid 
                sensors={sensors || []} 
                timeRange={selectedTimeRange}
                onSensorClick={(sensor) => {
                  // Ouvrir détails capteur ou naviguer vers XAI
                  if (onNavigateToXAI) onNavigateToXAI();
                }}
              />
            </Paper>
          </motion.div>
        </Grid>

        {/* Panneau d'alertes et métriques */}
        <Grid item xs={12} lg={4}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Alertes */}
              <Paper sx={{ p: 2, height: '280px' }}>
                <Typography variant="h6" fontWeight="medium" sx={{ mb: 2 }}>
                  <Badge badgeContent={sensorStats?.critical || 0} color="error">
                    Alertes Critiques
                  </Badge>
                </Typography>
                <AlertsPanel 
                  alerts={sensors?.filter(s => s.alertLevel !== 'normal') || []}
                  maxHeight={220}
                />
              </Paper>

              {/* Métriques système */}
              <Paper sx={{ p: 2, height: '300px' }}>
                <Typography variant="h6" fontWeight="medium" sx={{ mb: 2 }}>
                  Métriques Système
                </Typography>
                <MetricsOverview 
                  metrics={metrics}
                  compact={true}
                />
              </Paper>
            </Box>
          </motion.div>
        </Grid>

        {/* Graphiques temps réel */}
        <Grid item xs={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <Paper sx={{ p: 2, height: '400px' }}>
              <Typography variant="h6" fontWeight="medium" sx={{ mb: 2 }}>
                Tendances Temps Réel - Station Traffeyère
              </Typography>
              <RealTimeChart 
                data={sensors || []}
                height={340}
                showLegend={true}
                timeRange={selectedTimeRange}
              />
            </Paper>
          </motion.div>
        </Grid>
      </Grid>

      {/* Assistant vocal flottant */}
      <AnimatePresence>
        {onOpenVoiceAssistant && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            style={{
              position: 'fixed',
              bottom: 24,
              right: 24,
              zIndex: 1000,
            }}
          >
            <Tooltip title="Assistant Vocal XIA">
              <Fab
                color="secondary"
                onClick={onOpenVoiceAssistant}
                sx={{
                  background: 'linear-gradient(45deg, #FF6B6B, #4ECDC4)',
                  animation: 'pulse 2s infinite',
                  '@keyframes pulse': {
                    '0%': { transform: 'scale(1)' },
                    '50%': { transform: 'scale(1.05)' },
                    '100%': { transform: 'scale(1)' },
                  },
                }}
              >
                <VoiceChat />
              </Fab>
            </Tooltip>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
};

export default MainDashboard;