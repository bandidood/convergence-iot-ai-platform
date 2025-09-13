import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  Alert,
  CircularProgress,
  InputAdornment,
  Fade,
} from '@mui/material';
import {
  Send as SendIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  VolumeUp as VolumeUpIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface ConversationalInterfaceProps {
  aiHook: any;
  voiceRecognition: any;
  speechSynthesis: any;
  websocket: any;
  config: any;
  theme: any;
  onAction: (action: string, data?: any) => void;
  sensorData: any[];
  alerts: any[];
  anomalies: number;
}

const ConversationalInterface: React.FC<ConversationalInterfaceProps> = ({
  aiHook,
  voiceRecognition,
  speechSynthesis,
  websocket,
  config,
  theme,
  onAction,
  sensorData,
  alerts,
  anomalies,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Message d'accueil initial
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: 'welcome',
        text: `Bonjour ! Je suis XIA, votre assistant IA pour la Station Traffeyère. Je peux vous aider à analyser les données de vos ${sensorData.length} capteurs IoT, expliquer les anomalies détectées, et répondre à vos questions sur le système.`,
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);

      // Annonce vocale si disponible
      if (speechSynthesis.isSupported && config.iot.alertNotifications) {
        speechSynthesis.speak('Assistant XIA prêt pour la Station Traffeyère');
      }
    }
  }, [messages.length, sensorData.length, speechSynthesis, config]);

  // Auto-scroll vers le bas
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Gestion de l'envoi de message
  const handleSendMessage = useCallback(async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Création du contexte enrichi avec données IoT
      const context = {
        currentSensors: sensorData.length,
        activeSensors: sensorData.filter(s => s.status === 'online').length,
        anomalies,
        alerts: alerts.length,
        timestamp: new Date().toISOString(),
      };

      // Simulation de réponse IA (à remplacer par aiHook réel)
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulation latence

      let responseText = '';
      
      // Réponses contextuelles simples
      if (inputText.toLowerCase().includes('capteur') || inputText.toLowerCase().includes('sensor')) {
        responseText = `📊 Actuellement, ${context.activeSensors}/${context.currentSensors} capteurs sont en ligne. ${anomalies > 0 ? `⚠️ ${anomalies} anomalie(s) détectée(s).` : '✅ Tous les systèmes fonctionnent normalement.'}`;
      } else if (inputText.toLowerCase().includes('anomalie') || inputText.toLowerCase().includes('alerte')) {
        responseText = anomalies > 0 
          ? `🚨 J'ai détecté ${anomalies} anomalie(s) sur la station. Les capteurs concernés nécessitent votre attention. Souhaitez-vous que j'analyse les détails ?`
          : '✅ Aucune anomalie détectée actuellement. Tous les capteurs fonctionnent dans les paramètres normaux.';
      } else if (inputText.toLowerCase().includes('temperature') || inputText.toLowerCase().includes('température')) {
        const tempSensors = sensorData.filter(s => s.type === 'temperature');
        responseText = `🌡️ ${tempSensors.length} capteurs de température actifs. La température moyenne est stable.`;
      } else if (inputText.toLowerCase().includes('aide') || inputText.toLowerCase().includes('help')) {
        responseText = `🔧 Je peux vous aider avec :
        • État des capteurs IoT
        • Analyse des anomalies 
        • Explications des alertes
        • Navigation dans l'interface
        • Données temps réel
        
        Que souhaitez-vous savoir ?`;
      } else {
        responseText = `🤖 J'ai bien reçu votre message : "${inputText}". En tant qu'assistant IA de la Station Traffeyère, je peux analyser vos données IoT et vous aider avec le système. Pouvez-vous préciser ce dont vous avez besoin ?`;
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: responseText,
        sender: 'ai',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, aiMessage]);

      // Synthèse vocale si activée
      if (speechSynthesis.isSupported && config.voice.enabled) {
        await speechSynthesis.speak(responseText);
      }

    } catch (error) {
      console.error('Erreur envoi message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        text: 'Désolé, une erreur est survenue. Veuillez réessayer.',
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, sensorData, anomalies, alerts.length, speechSynthesis, config]);

  // Gestion du micro
  const handleMicToggle = useCallback(() => {
    if (voiceRecognition.listening) {
      voiceRecognition.stop();
    } else {
      voiceRecognition.start();
    }
  }, [voiceRecognition]);

  // Traitement transcript vocal
  useEffect(() => {
    if (voiceRecognition.finalTranscript) {
      setInputText(voiceRecognition.finalTranscript);
    }
  }, [voiceRecognition.finalTranscript]);

  // Effacer la conversation
  const handleClearConversation = () => {
    setMessages([]);
    onAction('clear-conversation');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Zone de messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <List>
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ListItem 
                  sx={{ 
                    justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                    mb: 1
                  }}
                >
                  <Paper
                    elevation={2}
                    sx={{
                      p: 2,
                      maxWidth: '75%',
                      bgcolor: message.sender === 'user' 
                        ? theme.messageUser 
                        : theme.messageAI,
                      color: 'white',
                      borderRadius: 3,
                      ...(message.sender === 'user' && {
                        borderBottomRightRadius: 8,
                      }),
                      ...(message.sender === 'ai' && {
                        borderBottomLeftRadius: 8,
                      }),
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Avatar 
                        sx={{ 
                          width: 24, 
                          height: 24, 
                          bgcolor: 'rgba(255,255,255,0.2)' 
                        }}
                      >
                        {message.sender === 'user' ? (
                          <PersonIcon sx={{ fontSize: 16 }} />
                        ) : (
                          <SmartToyIcon sx={{ fontSize: 16 }} />
                        )}
                      </Avatar>
                      <Typography variant="caption" sx={{ opacity: 0.8 }}>
                        {message.timestamp.toLocaleTimeString()}
                      </Typography>
                    </Box>
                    
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {message.text}
                    </Typography>
                  </Paper>
                </ListItem>
              </motion.div>
            ))}
          </AnimatePresence>
        </List>
        
        {/* Indicateur de saisie */}
        {isLoading && (
          <Fade in={isLoading}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                XIA réfléchit...
              </Typography>
            </Box>
          </Fade>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Zone de saisie */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 2, 
          m: 2, 
          bgcolor: 'rgba(255,255,255,0.95)',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Transcript vocal en cours */}
        {voiceRecognition.listening && voiceRecognition.transcript && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              🎤 "{voiceRecognition.transcript}"
            </Typography>
          </Alert>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Bouton micro */}
          <IconButton
            onClick={handleMicToggle}
            color={voiceRecognition.listening ? 'primary' : 'default'}
            disabled={!voiceRecognition.isSupported}
          >
            {voiceRecognition.listening ? <MicIcon /> : <MicOffIcon />}
          </IconButton>

          {/* Champ de saisie */}
          <TextField
            fullWidth
            variant="outlined"
            size="small"
            placeholder="Tapez votre message ou utilisez le micro..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            disabled={isLoading || voiceRecognition.listening}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleSendMessage}
                    disabled={!inputText.trim() || isLoading}
                    color="primary"
                  >
                    <SendIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* Contrôles additionnels */}
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton
              size="small"
              onClick={() => speechSynthesis.stop()}
              disabled={!speechSynthesis.speaking}
              title="Arrêter la synthèse"
            >
              <VolumeUpIcon />
            </IconButton>

            <IconButton
              size="small"
              onClick={handleClearConversation}
              title="Effacer la conversation"
            >
              <ClearIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Informations contextuelles */}
        <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
          <Chip 
            size="small" 
            label={`${sensorData.length} capteurs`} 
            color="primary" 
            variant="outlined" 
          />
          {anomalies > 0 && (
            <Chip 
              size="small" 
              label={`${anomalies} anomalie(s)`} 
              color="error" 
              variant="outlined" 
            />
          )}
          {websocket.isConnected && (
            <Chip 
              size="small" 
              label="Temps réel" 
              color="success" 
              variant="outlined" 
            />
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default ConversationalInterface;