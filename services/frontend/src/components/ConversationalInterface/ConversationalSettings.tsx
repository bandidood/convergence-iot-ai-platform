import React from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
  Divider,
  Chip,
  Card,
  CardContent,
  Button,
  IconButton,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  VolumeUp,
  VolumeOff,
  Mic,
  MicOff,
  Wifi,
  WifiOff,
  TestTube,
  Refresh,
  Psychology,
  Settings,
} from '@mui/icons-material';

interface ConversationalSettingsProps {
  config: any;
  onConfigChange: (newConfig: any) => void;
  voiceRecognition: any;
  speechSynthesis: any;
  websocket: any;
}

const ConversationalSettings: React.FC<ConversationalSettingsProps> = ({
  config,
  onConfigChange,
  voiceRecognition,
  speechSynthesis,
  websocket,
}) => {
  const handleProviderChange = (provider: string) => {
    onConfigChange({
      ...config,
      currentProvider: provider,
    });
  };

  const handleVoiceTest = async () => {
    if (speechSynthesis.isSupported) {
      await speechSynthesis.testSpeech('Test de synthèse vocale pour XIA Station Traffeyère');
    }
  };

  const handleMicTest = () => {
    if (voiceRecognition.isSupported) {
      voiceRecognition.start();
    }
  };

  return (
    <Box sx={{ p: 2, maxHeight: 300, overflow: 'auto' }}>
      {/* Provider IA */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Modèle IA
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {Object.keys(config.aiProviders).map((provider) => (
            <Chip
              key={provider}
              label={config.aiProviders[provider].displayName}
              onClick={() => handleProviderChange(provider)}
              color={config.currentProvider === provider ? 'primary' : 'default'}
              size="small"
              icon={<Psychology />}
              clickable
            />
          ))}
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Configuration Voix */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
          Paramètres Vocaux
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          {/* Test Synthèse */}
          <Card sx={{ flex: 1, bgcolor: 'rgba(76, 175, 80, 0.1)' }}>
            <CardContent sx={{ p: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <VolumeUp sx={{ fontSize: 16 }} />
                <Typography variant="caption">Synthèse</Typography>
              </Box>
              <Typography variant="body2" sx={{ fontSize: 11, mb: 1 }}>
                {speechSynthesis.isSupported ? 'Supportée' : 'Non supportée'}
              </Typography>
              <Button
                size="small"
                variant="outlined"
                onClick={handleVoiceTest}
                disabled={!speechSynthesis.isSupported || speechSynthesis.speaking}
                sx={{ fontSize: 10, py: 0.5 }}
              >
                Test
              </Button>
            </CardContent>
          </Card>

          {/* Test Reconnaissance */}
          <Card sx={{ flex: 1, bgcolor: 'rgba(33, 150, 243, 0.1)' }}>
            <CardContent sx={{ p: 1.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Mic sx={{ fontSize: 16 }} />
                <Typography variant="caption">Reconnaissance</Typography>
              </Box>
              <Typography variant="body2" sx={{ fontSize: 11, mb: 1 }}>
                {voiceRecognition.isSupported ? 'Supportée' : 'Non supportée'}
              </Typography>
              <Button
                size="small"
                variant="outlined"
                onClick={handleMicTest}
                disabled={!voiceRecognition.isSupported || voiceRecognition.listening}
                sx={{ fontSize: 10, py: 0.5 }}
              >
                {voiceRecognition.listening ? 'Écoute...' : 'Test'}
              </Button>
            </CardContent>
          </Card>
        </Box>

        {/* Contrôles Voix */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box>
            <Typography variant="caption" sx={{ fontSize: 11 }}>
              Vitesse ({config.voice.synthesis.rate}x)
            </Typography>
            <Slider
              size="small"
              value={config.voice.synthesis.rate}
              onChange={(_, value) => onConfigChange({
                ...config,
                voice: {
                  ...config.voice,
                  synthesis: { ...config.voice.synthesis, rate: value }
                }
              })}
              min={0.5}
              max={2.0}
              step={0.1}
              sx={{ height: 4 }}
            />
          </Box>

          <Box>
            <Typography variant="caption" sx={{ fontSize: 11 }}>
              Volume ({Math.round(config.voice.synthesis.volume * 100)}%)
            </Typography>
            <Slider
              size="small"
              value={config.voice.synthesis.volume}
              onChange={(_, value) => onConfigChange({
                ...config,
                voice: {
                  ...config.voice,
                  synthesis: { ...config.voice.synthesis, volume: value }
                }
              })}
              min={0}
              max={1}
              step={0.1}
              sx={{ height: 4 }}
            />
          </Box>
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Statut WebSocket */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Connexion Temps Réel
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            icon={websocket.isConnected ? <Wifi /> : <WifiOff />}
            label={websocket.isConnected ? 'Connecté' : 'Déconnecté'}
            color={websocket.isConnected ? 'success' : 'error'}
            size="small"
          />
          
          <Typography variant="caption" sx={{ fontSize: 11 }}>
            {websocket.messageHistory.length} messages reçus
          </Typography>
          
          {websocket.reconnectAttempts > 0 && (
            <Typography variant="caption" sx={{ fontSize: 11, color: 'warning.main' }}>
              Tentatives: {websocket.reconnectAttempts}
            </Typography>
          )}
        </Box>

        {websocket.error && (
          <Alert severity="warning" sx={{ mt: 1, py: 0.5 }}>
            <Typography variant="caption">{websocket.error}</Typography>
          </Alert>
        )}
      </Box>

      <Divider sx={{ my: 2 }} />

      {/* Options Interface */}
      <Box>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
          Interface
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          <FormControlLabel
            control={
              <Switch
                size="small"
                checked={config.ui.animations}
                onChange={(e) => onConfigChange({
                  ...config,
                  ui: { ...config.ui, animations: e.target.checked }
                })}
              />
            }
            label={<Typography variant="caption">Animations</Typography>}
          />
          
          <FormControlLabel
            control={
              <Switch
                size="small"
                checked={config.ui.autoSaveHistory}
                onChange={(e) => onConfigChange({
                  ...config,
                  ui: { ...config.ui, autoSaveHistory: e.target.checked }
                })}
              />
            }
            label={<Typography variant="caption">Sauvegarde auto</Typography>}
          />
          
          <FormControlLabel
            control={
              <Switch
                size="small"
                checked={config.iot.alertNotifications}
                onChange={(e) => onConfigChange({
                  ...config,
                  iot: { ...config.iot, alertNotifications: e.target.checked }
                })}
              />
            }
            label={<Typography variant="caption">Alertes vocales</Typography>}
          />
        </Box>
      </Box>

      {/* Informations système */}
      <Box sx={{ mt: 2, p: 1, bgcolor: 'rgba(0,0,0,0.05)', borderRadius: 1 }}>
        <Typography variant="caption" sx={{ fontSize: 10, color: 'text.secondary' }}>
          Voix: {speechSynthesis.voices.length} disponibles • 
          Langue: {config.voice.defaultLanguage} • 
          Modèle: {config.aiProviders[config.currentProvider || 'claude']?.displayName}
        </Typography>
      </Box>
    </Box>
  );
};

export default ConversationalSettings;