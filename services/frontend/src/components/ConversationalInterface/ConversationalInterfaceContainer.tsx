import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Paper,
  IconButton,
  Typography,
  Chip,
  Alert,
  Tooltip,
  Fade,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Chat as ChatIcon,
  Minimize as MinimizeIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  Settings as SettingsIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

// Hooks personnalisés
import { useConversationalAI } from '../../hooks/useConversationalAI';
import { useVoiceRecognition } from '../../hooks/useVoiceRecognition';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { useWebSocket } from '../../hooks/useWebSocket';

// Configuration
import {
  defaultConversationalConfig,
  ConversationalConfig,
  automaticResponses,
  conversationalThemes,
} from '../../config/conversationalConfig';

// Composants enfants
import ConversationalInterface from './ConversationalInterface';
import ConversationalSettings from './ConversationalSettings';
import VoiceIndicator from './VoiceIndicator';

interface ConversationalInterfaceContainerProps {
  config?: Partial<ConversationalConfig>;
  sensorData?: any[];
  alerts?: any[];
  anomalies?: number;
  onAction?: (action: string, data?: any) => void;
  isMinimized?: boolean;
  onMinimizedChange?: (minimized: boolean) => void;
  position?: 'bottom-right' | 'bottom-left' | 'center' | 'fullscreen';
}

const ConversationalInterfaceContainer: React.FC<ConversationalInterfaceContainerProps> = ({
  config: customConfig = {},
  sensorData = [],
  alerts = [],
  anomalies = 0,
  onAction,
  isMinimized: externalMinimized,
  onMinimizedChange,
  position = 'bottom-right',
}) => {
  // Configuration fusionnée
  const config = useMemo(() => ({
    ...defaultConversationalConfig,
    ...customConfig,
  }), [customConfig]);

  // État local
  const [internalMinimized, setInternalMinimized] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(position === 'fullscreen');
  const [showSettings, setShowSettings] = useState(false);
  const [contextualAlerts, setContextualAlerts] = useState<string[]>([]);

  // Utilisation de l'état minimisé externe ou interne
  const isMinimized = externalMinimized ?? internalMinimized;
  const setMinimized = useCallback((minimized: boolean) => {
    if (onMinimizedChange) {
      onMinimizedChange(minimized);
    } else {
      setInternalMinimized(minimized);
    }
  }, [onMinimizedChange]);

  // Hooks Material-UI
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Hooks personnalisés
  const aiHook = useConversationalAI({
    provider: 'claude',
    config: config.aiProviders.claude,
    sensorData,
    alerts,
  });

  const voiceRecognition = useVoiceRecognition({
    language: config.voice.defaultLanguage,
    continuous: config.voice.recognition.continuous,
    interimResults: config.voice.recognition.interimResults,
    grammars: config.voice.recognition.grammars,
  });

  const speechSynthesis = useSpeechSynthesis({
    lang: config.voice.defaultLanguage,
    rate: config.voice.synthesis.rate,
    pitch: config.voice.synthesis.pitch,
    volume: config.voice.synthesis.volume,
  });

  const websocket = useWebSocket(
    config.websocket.enabled ? config.websocket.url : null,
    {
      reconnect: true,
      reconnectInterval: config.websocket.reconnectInterval,
      maxReconnectAttempts: config.websocket.maxReconnectAttempts,
      heartbeatInterval: config.websocket.heartbeatInterval,
    }
  );

  // Gestion des alertes contextuelles
  useEffect(() => {
    if (!config.iot.alertNotifications) return;

    const newAlerts: string[] = [];

    // Vérification température élevée
    const highTempSensors = sensorData.filter(
      sensor => sensor.type === 'temperature' && sensor.value > 35
    );
    highTempSensors.forEach(sensor => {
      newAlerts.push(automaticResponses.highTemperature(sensor.value));
    });

    // Capteurs hors ligne
    const offlineSensors = sensorData.filter(sensor => sensor.status === 'offline');
    offlineSensors.forEach(sensor => {
      newAlerts.push(automaticResponses.sensorOffline(sensor.id, sensor.name));
    });

    // Batteries faibles
    const lowBatterySensors = sensorData.filter(
      sensor => sensor.battery && sensor.battery < 20
    );
    lowBatterySensors.forEach(sensor => {
      newAlerts.push(automaticResponses.batteryLow(sensor.id, sensor.battery));
    });

    // Anomalies détectées
    if (anomalies > 0) {
      newAlerts.push(`🚨 ${anomalies} anomalie${anomalies > 1 ? 's détectées' : ' détectée'} nécessitant votre attention.`);
    }

    setContextualAlerts(newAlerts);

    // Annonce vocale des alertes critiques
    if (newAlerts.length > 0 && !isMinimized) {
      const criticalAlerts = newAlerts.filter(alert => 
        alert.includes('🚨') || alert.includes('⚠️')
      );
      
      if (criticalAlerts.length > 0 && speechSynthesis.isSupported) {
        const alertMessage = `${criticalAlerts.length} alerte${criticalAlerts.length > 1 ? 's' : ''} critique${criticalAlerts.length > 1 ? 's' : ''} détectée${criticalAlerts.length > 1 ? 's' : ''}`;
        speechSynthesis.announceAlert(alertMessage, 'high');
      }
    }
  }, [sensorData, anomalies, config.iot.alertNotifications, isMinimized, speechSynthesis]);

  // Gestion des messages WebSocket
  useEffect(() => {
    if (!websocket.lastMessage || !config.iot.realTimeUpdates) return;

    const message = websocket.lastMessage;
    
    // Traitement des messages IoT en temps réel
    if (message.type === 'sensor-update') {
      console.log('📊 Mise à jour capteur en temps réel:', message.data);
      // Intégrer avec aiHook si nécessaire
    } else if (message.type === 'alert') {
      console.log('🚨 Alerte temps réel:', message.data);
      if (speechSynthesis.isSupported && !isMinimized) {
        speechSynthesis.announceAlert(message.data.message, message.data.severity);
      }
    }
  }, [websocket.lastMessage, config.iot.realTimeUpdates, speechSynthesis, isMinimized]);

  // Actions personnalisées
  const handleAction = useCallback((action: string, data?: any) => {
    console.log('🎬 Action conversationnelle:', action, data);

    switch (action) {
      case 'minimize':
        setMinimized(true);
        break;
      case 'maximize':
        setMinimized(false);
        break;
      case 'fullscreen':
        setIsFullscreen(!isFullscreen);
        break;
      case 'settings':
        setShowSettings(!showSettings);
        break;
      case 'voice-toggle':
        if (voiceRecognition.listening) {
          voiceRecognition.stop();
        } else {
          voiceRecognition.start();
        }
        break;
      case 'speech-toggle':
        if (speechSynthesis.speaking) {
          speechSynthesis.stop();
        } else {
          speechSynthesis.testSpeech();
        }
        break;
      case 'sensor-status':
        const activeSensors = sensorData.filter(s => s.status === 'online').length;
        speechSynthesis.speakIoTData(sensorData, anomalies);
        break;
      default:
        onAction?.(action, data);
    }
  }, [
    setMinimized, isFullscreen, showSettings, voiceRecognition, 
    speechSynthesis, sensorData, anomalies, onAction
  ]);

  // Styles adaptatifs
  const getContainerStyles = useCallback(() => {
    const baseStyles = {
      position: 'fixed' as const,
      zIndex: 1300,
      transition: 'all 0.3s ease-in-out',
    };

    if (isFullscreen) {
      return {
        ...baseStyles,
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        borderRadius: 0,
      };
    }

    if (isMinimized) {
      const miniSize = isMobile ? 60 : 80;
      return {
        ...baseStyles,
        width: miniSize,
        height: miniSize,
        borderRadius: '50%',
        ...(position === 'bottom-right' && {
          bottom: isMobile ? 20 : 30,
          right: isMobile ? 20 : 30,
        }),
        ...(position === 'bottom-left' && {
          bottom: isMobile ? 20 : 30,
          left: isMobile ? 20 : 30,
        }),
      };
    }

    const normalSize = isMobile 
      ? { width: '95vw', height: '70vh' }
      : { width: 450, height: 600 };

    return {
      ...baseStyles,
      ...normalSize,
      borderRadius: 2,
      ...(position === 'bottom-right' && {
        bottom: isMobile ? 20 : 30,
        right: isMobile ? 20 : 30,
      }),
      ...(position === 'bottom-left' && {
        bottom: isMobile ? 20 : 30,
        left: isMobile ? 20 : 30,
      }),
      ...(position === 'center' && {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      }),
    };
  }, [isFullscreen, isMinimized, position, isMobile]);

  // Thème visuel
  const activeTheme = useMemo(() => {
    const themeKey = config.ui.theme === 'auto' 
      ? (theme.palette.mode === 'dark' ? 'dark' : 'light')
      : config.ui.theme;
    return conversationalThemes[themeKey] || conversationalThemes.light;
  }, [config.ui.theme, theme.palette.mode]);

  // Rendu minimisé
  if (isMinimized) {
    return (
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        style={getContainerStyles()}
      >
        <Paper
          elevation={8}
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: activeTheme.background,
            color: activeTheme.text,
            cursor: 'pointer',
            position: 'relative',
            overflow: 'hidden',
          }}
          onClick={() => handleAction('maximize')}
        >
          <ChatIcon sx={{ fontSize: isMobile ? 28 : 36 }} />
          
          {/* Indicateur de nouvelles alertes */}
          <AnimatePresence>
            {contextualAlerts.length > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                style={{
                  position: 'absolute',
                  top: -5,
                  right: -5,
                  background: '#f44336',
                  color: 'white',
                  borderRadius: '50%',
                  minWidth: 20,
                  height: 20,
                  fontSize: 12,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                }}
              >
                {contextualAlerts.length}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Indicateur vocal */}
          <VoiceIndicator
            listening={voiceRecognition.listening}
            speaking={speechSynthesis.speaking}
            size="small"
            style={{
              position: 'absolute',
              bottom: -10,
              right: -10,
            }}
          />
        </Paper>
      </motion.div>
    );
  }

  // Rendu principal
  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      style={getContainerStyles()}
    >
      <Paper
        elevation={12}
        sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          background: activeTheme.background,
          color: activeTheme.text,
          overflow: 'hidden',
        }}
      >
        {/* En-tête */}
        <Box
          sx={{
            p: 2,
            borderBottom: `1px solid ${activeTheme.border}`,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            background: 'rgba(255,255,255,0.1)',
          }}
        >
          <ChatIcon sx={{ color: activeTheme.accent }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
            XIA - Assistant IoT
          </Typography>

          {/* Indicateurs d'état */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            {websocket.isConnected && (
              <Chip
                size="small"
                label="Live"
                color="success"
                sx={{ fontSize: 10 }}
              />
            )}
            {anomalies > 0 && (
              <Chip
                size="small"
                label={`${anomalies} Anomalie${anomalies > 1 ? 's' : ''}`}
                color="error"
                sx={{ fontSize: 10 }}
              />
            )}
          </Box>

          {/* Contrôles */}
          <Tooltip title="Synthèse vocale">
            <IconButton
              size="small"
              onClick={() => handleAction('speech-toggle')}
              color={speechSynthesis.speaking ? 'primary' : 'default'}
            >
              {speechSynthesis.isSupported ? <VolumeUpIcon /> : <VolumeOffIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Paramètres">
            <IconButton
              size="small"
              onClick={() => handleAction('settings')}
              color={showSettings ? 'primary' : 'default'}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Plein écran">
            <IconButton
              size="small"
              onClick={() => handleAction('fullscreen')}
            >
              {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Réduire">
            <IconButton
              size="small"
              onClick={() => handleAction('minimize')}
            >
              <MinimizeIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Alertes contextuelles */}
        <AnimatePresence>
          {contextualAlerts.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
            >
              <Box sx={{ p: 1, maxHeight: 120, overflow: 'auto' }}>
                {contextualAlerts.slice(0, 3).map((alert, index) => (
                  <Alert
                    key={index}
                    severity={alert.includes('🚨') ? 'error' : 'warning'}
                    size="small"
                    sx={{ mb: 0.5, fontSize: 12 }}
                  >
                    {alert}
                  </Alert>
                ))}
              </Box>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Paramètres */}
        <AnimatePresence>
          {showSettings && (
            <Fade in={showSettings}>
              <Box>
                <ConversationalSettings
                  config={config}
                  onConfigChange={() => {}}
                  voiceRecognition={voiceRecognition}
                  speechSynthesis={speechSynthesis}
                  websocket={websocket}
                />
              </Box>
            </Fade>
          )}
        </AnimatePresence>

        {/* Interface principale */}
        <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
          <ConversationalInterface
            aiHook={aiHook}
            voiceRecognition={voiceRecognition}
            speechSynthesis={speechSynthesis}
            websocket={websocket}
            config={config}
            theme={activeTheme}
            onAction={handleAction}
            sensorData={sensorData}
            alerts={alerts}
            anomalies={anomalies}
          />
        </Box>

        {/* Indicateur vocal flottant */}
        <VoiceIndicator
          listening={voiceRecognition.listening}
          speaking={speechSynthesis.speaking}
          error={voiceRecognition.error || speechSynthesis.error}
          style={{
            position: 'absolute',
            bottom: 20,
            right: 20,
            zIndex: 10,
          }}
        />
      </Paper>
    </motion.div>
  );
};

export default ConversationalInterfaceContainer;