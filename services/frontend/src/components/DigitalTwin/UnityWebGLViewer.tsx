import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Fab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Card,
  CardContent,
  Chip,
  Grid,
  Slider,
  Switch,
  FormControlLabel,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  Alert,
} from '@mui/material';
import {
  ThreeDRotation,
  Fullscreen,
  FullscreenExit,
  CameraAlt,
  VideoCall,
  VrPtz,
  Settings,
  Refresh,
  PlayArrow,
  Pause,
  Speed,
  Visibility,
  VisibilityOff,
  ViewInAr,
  Home,
  ZoomIn,
  ZoomOut,
  RotateLeft,
  RotateRight,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

import { useDigitalTwin } from '@hooks/useDigitalTwin';
import { useIoTData } from '@hooks/useIoTData';
import { useWebSocket } from '@hooks/useWebSocket';
import TwinControlPanel from './TwinControlPanel';
import ARVRInterface from './ARVRInterface';
import SimulationControls from './SimulationControls';
import { DigitalTwinState, CameraPosition, SimulationData } from '@types/twin.types';

interface UnityWebGLViewerProps {
  width?: string | number;
  height?: string | number;
  autoSync?: boolean;
  enableVR?: boolean;
  showControls?: boolean;
  onStateChange?: (state: DigitalTwinState) => void;
}

const UnityWebGLViewer: React.FC<UnityWebGLViewerProps> = ({
  width = '100%',
  height = '600px',
  autoSync = true,
  enableVR = true,
  showControls = true,
  onStateChange,
}) => {
  const unityContainerRef = useRef<HTMLDivElement>(null);
  const unityInstanceRef = useRef<any>(null);
  
  const [isLoaded, setIsLoaded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [simulationSpeed, setSimulationSpeed] = useState(1.0);
  const [cameraPosition, setCameraPosition] = useState<CameraPosition>('overview');
  const [showUI, setShowUI] = useState(true);
  const [vrMode, setVrMode] = useState(false);
  const [showARDialog, setShowARDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(0);

  // Hooks personnalisés
  const {
    twinState,
    isConnected,
    sendCommand,
    updateSimulation,
    cameraControls,
    loading
  } = useDigitalTwin();
  
  const { sensors } = useIoTData();
  const { isConnected: wsConnected } = useWebSocket('ws://backend:8000/ws/digital-twin');

  // Initialisation Unity WebGL
  useEffect(() => {
    const initUnity = async () => {
      if (!unityContainerRef.current) return;

      try {
        // Configuration Unity
        const config = {
          dataUrl: '/unity/Build/StationTraffeyereDigitalTwin.data',
          frameworkUrl: '/unity/Build/StationTraffeyereDigitalTwin.framework.js',
          codeUrl: '/unity/Build/StationTraffeyereDigitalTwin.wasm',
          streamingAssetsUrl: '/unity/StreamingAssets',
          companyName: 'StationTraffeyere',
          productName: 'DigitalTwinViewer',
          productVersion: '2.1.3',
          showBanner: false,
          matchWebGLToCanvasSize: false,
          devicePixelRatio: 1,
        };

        // Callbacks de progression
        const progressCallback = (progress: number) => {
          setLoadingProgress(Math.round(progress * 100));
        };

        // Chargement Unity
        const unityInstance = await (window as any).createUnityInstance(
          unityContainerRef.current,
          config,
          progressCallback
        );

        unityInstanceRef.current = unityInstance;
        setIsLoaded(true);
        setError(null);

        // Configuration initiale
        await configureUnityInstance();

        console.log('Unity Digital Twin initialisé avec succès');

      } catch (err) {
        console.error('Erreur initialisation Unity:', err);
        setError('Impossible de charger le Digital Twin Unity');
      }
    };

    if (unityContainerRef.current && !isLoaded) {
      initUnity();
    }

    return () => {
      if (unityInstanceRef.current) {
        unityInstanceRef.current.Quit();
      }
    };
  }, []);

  // Configuration Unity après chargement
  const configureUnityInstance = useCallback(async () => {
    if (!unityInstanceRef.current) return;

    try {
      // Configuration caméra initiale
      await unityInstanceRef.current.SendMessage(
        'CameraController',
        'SetCameraPosition',
        JSON.stringify({ position: cameraPosition, smooth: true })
      );

      // Configuration visualisation
      await unityInstanceRef.current.SendMessage(
        'SceneManager',
        'SetVisualizationMode',
        'realistic'
      );

      // Activation synchronisation IoT si demandée
      if (autoSync) {
        await unityInstanceRef.current.SendMessage(
          'IoTSync',
          'EnableAutoSync',
          'true'
        );
      }

      console.log('Unity configuré avec succès');

    } catch (err) {
      console.error('Erreur configuration Unity:', err);
    }
  }, [cameraPosition, autoSync]);

  // Synchronisation données IoT en temps réel
  useEffect(() => {
    if (!isLoaded || !unityInstanceRef.current || !sensors || !autoSync) return;

    const syncIoTData = async () => {
      try {
        // Préparation données pour Unity
        const sensorData = sensors.map(sensor => ({
          id: sensor.id,
          name: sensor.name,
          type: sensor.type,
          value: sensor.value,
          status: sensor.status,
          position: sensor.position,
          alertLevel: sensor.alertLevel,
          hasAnomaly: sensor.hasAnomaly,
          timestamp: sensor.lastUpdate,
        }));

        // Envoi vers Unity
        await unityInstanceRef.current.SendMessage(
          'IoTDataManager',
          'UpdateSensorData',
          JSON.stringify(sensorData)
        );

        // Mise à jour état simulation
        onStateChange?.({
          ...twinState,
          lastSyncTime: new Date(),
          connectedSensors: sensors.filter(s => s.status === 'online').length,
          totalSensors: sensors.length,
        } as DigitalTwinState);

      } catch (err) {
        console.error('Erreur synchronisation IoT:', err);
      }
    };

    // Synchronisation initiale puis toutes les 5 secondes
    syncIoTData();
    const interval = setInterval(syncIoTData, 5000);

    return () => clearInterval(interval);
  }, [isLoaded, sensors, autoSync, twinState, onStateChange]);

  // Contrôles caméra
  const handleCameraControl = useCallback(async (action: string, params?: any) => {
    if (!unityInstanceRef.current) return;

    try {
      switch (action) {
        case 'setPosition':
          setCameraPosition(params.position);
          await unityInstanceRef.current.SendMessage(
            'CameraController',
            'SetCameraPosition',
            JSON.stringify(params)
          );
          break;

        case 'zoom':
          await unityInstanceRef.current.SendMessage(
            'CameraController',
            'ZoomCamera',
            params.delta.toString()
          );
          break;

        case 'rotate':
          await unityInstanceRef.current.SendMessage(
            'CameraController',
            'RotateCamera',
            JSON.stringify(params)
          );
          break;

        case 'reset':
          setCameraPosition('overview');
          await unityInstanceRef.current.SendMessage(
            'CameraController',
            'ResetCamera',
            ''
          );
          break;
      }
    } catch (err) {
      console.error('Erreur contrôle caméra:', err);
    }
  }, []);

  // Contrôles simulation
  const handleSimulationControl = useCallback(async (action: string, params?: any) => {
    if (!unityInstanceRef.current) return;

    try {
      switch (action) {
        case 'play':
          setIsPlaying(true);
          await unityInstanceRef.current.SendMessage('SimulationManager', 'Play', '');
          break;

        case 'pause':
          setIsPlaying(false);
          await unityInstanceRef.current.SendMessage('SimulationManager', 'Pause', '');
          break;

        case 'setSpeed':
          setSimulationSpeed(params.speed);
          await unityInstanceRef.current.SendMessage(
            'SimulationManager',
            'SetSpeed',
            params.speed.toString()
          );
          break;

        case 'reset':
          await unityInstanceRef.current.SendMessage('SimulationManager', 'Reset', '');
          break;
      }
    } catch (err) {
      console.error('Erreur contrôle simulation:', err);
    }
  }, []);

  // Mode plein écran
  const handleFullscreenToggle = useCallback(async () => {
    if (!unityContainerRef.current) return;

    try {
      if (isFullscreen) {
        await document.exitFullscreen();
        setIsFullscreen(false);
      } else {
        await unityContainerRef.current.requestFullscreen();
        setIsFullscreen(true);
      }
    } catch (err) {
      console.error('Erreur mode plein écran:', err);
    }
  }, [isFullscreen]);

  // Capture d'écran
  const handleScreenshot = useCallback(async () => {
    if (!unityInstanceRef.current) return;

    try {
      await unityInstanceRef.current.SendMessage('ScreenshotManager', 'TakeScreenshot', '');
    } catch (err) {
      console.error('Erreur capture d\'écran:', err);
    }
  }, []);

  // Mode VR/AR
  const handleVRToggle = useCallback(async () => {
    if (!unityInstanceRef.current) return;

    try {
      if (vrMode) {
        await unityInstanceRef.current.SendMessage('VRManager', 'ExitVR', '');
        setVrMode(false);
      } else {
        await unityInstanceRef.current.SendMessage('VRManager', 'EnterVR', '');
        setVrMode(true);
      }
    } catch (err) {
      console.error('Erreur mode VR:', err);
    }
  }, [vrMode]);

  if (error) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={() => window.location.reload()}>
          Recharger
        </Button>
      </Paper>
    );
  }

  return (
    <Box sx={{ position: 'relative', width, height }}>
      {/* Container Unity */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        style={{
          width: '100%',
          height: '100%',
          position: 'relative',
          borderRadius: 8,
          overflow: 'hidden',
          background: '#000',
        }}
      >
        <div
          ref={unityContainerRef}
          style={{
            width: '100%',
            height: '100%',
            position: 'relative',
          }}
        />

        {/* Indicateur de chargement */}
        {!isLoaded && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              bgcolor: 'rgba(0,0,0,0.8)',
              color: 'white',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2 }}>
              Chargement Digital Twin Unity...
            </Typography>
            <Box sx={{ width: '60%', mb: 2 }}>
              <Typography variant="body2" sx={{ mb: 1, textAlign: 'center' }}>
                {loadingProgress}%
              </Typography>
              <Box
                sx={{
                  width: '100%',
                  height: 8,
                  bgcolor: 'rgba(255,255,255,0.2)',
                  borderRadius: 4,
                }}
              >
                <Box
                  sx={{
                    width: `${loadingProgress}%`,
                    height: '100%',
                    bgcolor: 'primary.main',
                    borderRadius: 4,
                    transition: 'width 0.3s ease',
                  }}
                />
              </Box>
            </Box>
          </Box>
        )}

        {/* Overlay informations */}
        <AnimatePresence>
          {showUI && isLoaded && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              style={{
                position: 'absolute',
                top: 16,
                left: 16,
                zIndex: 10,
              }}
            >
              <Card sx={{ bgcolor: 'rgba(0,0,0,0.7)', color: 'white' }}>
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <ThreeDRotation sx={{ fontSize: 20 }} />
                    <Typography variant="h6">Digital Twin - Station Traffeyère</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip
                      size="small"
                      label={`IoT: ${twinState?.connectedSensors || 0}/${twinState?.totalSensors || 127}`}
                      color={wsConnected ? 'success' : 'error'}
                    />
                    <Chip
                      size="small"
                      label={`Caméra: ${cameraPosition}`}
                      color="info"
                    />
                    <Chip
                      size="small"
                      label={isPlaying ? 'En cours' : 'Pause'}
                      color={isPlaying ? 'success' : 'warning'}
                    />
                    <Chip
                      size="small"
                      label={`Vitesse: ${simulationSpeed}x`}
                      color="secondary"
                    />
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Contrôles principaux */}
        {showControls && isLoaded && (
          <>
            {/* Contrôles plein écran et UI */}
            <Box
              sx={{
                position: 'absolute',
                top: 16,
                right: 16,
                display: 'flex',
                gap: 1,
                zIndex: 10,
              }}
            >
              <Tooltip title="Masquer/Afficher UI">
                <IconButton
                  sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
                  onClick={() => setShowUI(!showUI)}
                >
                  {showUI ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </Tooltip>

              <Tooltip title={isFullscreen ? 'Quitter plein écran' : 'Plein écran'}>
                <IconButton
                  sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
                  onClick={handleFullscreenToggle}
                >
                  {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
                </IconButton>
              </Tooltip>
            </Box>

            {/* Contrôles caméra */}
            <Box
              sx={{
                position: 'absolute',
                bottom: 80,
                right: 16,
                display: 'flex',
                flexDirection: 'column',
                gap: 1,
                zIndex: 10,
              }}
            >
              <Tooltip title="Zoom avant">
                <IconButton
                  sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
                  onClick={() => handleCameraControl('zoom', { delta: 1 })}
                >
                  <ZoomIn />
                </IconButton>
              </Tooltip>

              <Tooltip title="Zoom arrière">
                <IconButton
                  sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
                  onClick={() => handleCameraControl('zoom', { delta: -1 })}
                >
                  <ZoomOut />
                </IconButton>
              </Tooltip>

              <Tooltip title="Réinitialiser caméra">
                <IconButton
                  sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
                  onClick={() => handleCameraControl('reset')}
                >
                  <Home />
                </IconButton>
              </Tooltip>
            </Box>

            {/* Menu d'actions rapides */}
            <SpeedDial
              ariaLabel="Actions Digital Twin"
              sx={{ position: 'absolute', bottom: 16, right: 16 }}
              icon={<SpeedDialIcon />}
              direction="up"
            >
              <SpeedDialAction
                key="screenshot"
                icon={<CameraAlt />}
                tooltipTitle="Capture d'écran"
                onClick={handleScreenshot}
              />
              
              <SpeedDialAction
                key="simulation"
                icon={isPlaying ? <Pause /> : <PlayArrow />}
                tooltipTitle={isPlaying ? 'Pause' : 'Lecture'}
                onClick={() => handleSimulationControl(isPlaying ? 'pause' : 'play')}
              />

              {enableVR && (
                <SpeedDialAction
                  key="vr"
                  icon={<VrPtz />}
                  tooltipTitle="Mode VR"
                  onClick={handleVRToggle}
                />
              )}

              <SpeedDialAction
                key="ar"
                icon={<ViewInAr />}
                tooltipTitle="Mode AR"
                onClick={() => setShowARDialog(true)}
              />

              <SpeedDialAction
                key="settings"
                icon={<Settings />}
                tooltipTitle="Paramètres"
                onClick={() => {/* Ouvrir panneau paramètres */}}
              />
            </SpeedDial>

            {/* Contrôles simulation en bas */}
            {showUI && (
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 16,
                  left: 16,
                  right: 100,
                  zIndex: 10,
                }}
              >
                <SimulationControls
                  isPlaying={isPlaying}
                  speed={simulationSpeed}
                  onPlayPause={() => handleSimulationControl(isPlaying ? 'pause' : 'play')}
                  onSpeedChange={(speed) => handleSimulationControl('setSpeed', { speed })}
                  onReset={() => handleSimulationControl('reset')}
                />
              </Box>
            )}
          </>
        )}
      </motion.div>

      {/* Dialog AR/VR */}
      <Dialog open={showARDialog} onClose={() => setShowARDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Interface AR/VR</DialogTitle>
        <DialogContent>
          <ARVRInterface
            unityInstance={unityInstanceRef.current}
            onClose={() => setShowARDialog(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default UnityWebGLViewer;