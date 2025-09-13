import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Fab,
  Avatar,
  Chip,
  Card,
  CardContent,
  LinearProgress,
  Tooltip,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Dialog,
  DialogTitle,
  DialogContent,
  Alert,
  Divider,
  Button,
} from '@mui/material';
import {
  Mic,
  MicOff,
  VolumeUp,
  VolumeOff,
  Send,
  SmartToy,
  Psychology,
  Clear,
  Settings,
  History,
  Translate,
  Speed,
  AutoFixHigh,
  Science,
  Insights,
  Chat,
  Close,
  PlayArrow,
  Pause,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { styled } from '@mui/material/styles';

import { useVoiceRecognition } from '@hooks/useVoiceRecognition';
import { useSpeechSynthesis } from '@hooks/useSpeechSynthesis';
import { useConversationalAI } from '@hooks/useConversationalAI';
import { useXAIExplanations } from '@hooks/useXAIExplanations';
import { useIoTData } from '@hooks/useIoTData';
import VoiceCommands from './VoiceCommands';
import ConversationHistory from './ConversationHistory';
import AIPersonalitySelector from './AIPersonalitySelector';
import { 
  ConversationMessage, 
  VoiceCommand, 
  AIProvider,
  ConversationContext 
} from '@types/conversation.types';

// Styled Components
const VoiceButton = styled(Fab)(({ theme, isListening }: { theme: any, isListening: boolean }) => ({
  background: isListening 
    ? 'linear-gradient(45deg, #ff6b6b 30%, #feca57 90%)'
    : 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
  color: 'white',
  animation: isListening ? 'pulse 1.5s ease-in-out infinite alternate' : 'none',
  '&:hover': {
    transform: 'scale(1.1)',
  },
  '@keyframes pulse': {
    from: { transform: 'scale(1)' },
    to: { transform: 'scale(1.05)' },
  },
}));

const MessageBubble = styled(Card)(({ theme, isUser }: { theme: any, isUser: boolean }) => ({
  margin: theme.spacing(1, 0),
  marginLeft: isUser ? theme.spacing(4) : 0,
  marginRight: isUser ? 0 : theme.spacing(4),
  background: isUser 
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  color: 'white',
  borderRadius: theme.spacing(2),
}));

const AudioWaveform = styled(Box)(({ theme, amplitude }: { theme: any, amplitude: number }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: theme.spacing(0.5),
  '& .wave-bar': {
    width: 3,
    backgroundColor: theme.palette.primary.main,
    borderRadius: 2,
    transition: 'height 0.1s ease',
  },
}));

interface ConversationalInterfaceProps {
  isOpen?: boolean;
  onClose?: () => void;
  initialContext?: ConversationContext;
  expertiseLevel?: 'novice' | 'intermediate' | 'expert' | 'researcher';
}

const ConversationalInterface: React.FC<ConversationalInterfaceProps> = ({
  isOpen = false,
  onClose,
  initialContext,
  expertiseLevel = 'intermediate',
}) => {
  // États principaux
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentMessage, setCurrentMessage] = useState('');
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [selectedAI, setSelectedAI] = useState<AIProvider>('gemini');
  const [language, setLanguage] = useState<'fr' | 'en'>('fr');
  const [speechRate, setSpeechRate] = useState(1.0);
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Hooks personnalisés
  const {
    isSupported: voiceSupported,
    isListening: voiceListening,
    transcript,
    confidence,
    startListening,
    stopListening,
    resetTranscript,
  } = useVoiceRecognition({
    language: language === 'fr' ? 'fr-FR' : 'en-US',
    continuous: true,
    interimResults: true,
  });

  const {
    speak,
    stop: stopSpeaking,
    speaking,
    voices,
    selectedVoice,
    setVoice,
  } = useSpeechSynthesis({
    rate: speechRate,
    pitch: 1.0,
    volume: 0.8,
    lang: language === 'fr' ? 'fr-FR' : 'en-US',
  });

  const {
    sendMessage,
    loading: aiLoading,
    conversation: aiConversation,
    clearConversation,
    setProvider,
    contextData,
  } = useConversationalAI({
    provider: selectedAI,
    expertiseLevel,
    context: initialContext,
  });

  const { sensors, metrics } = useIoTData();
  const { explanation } = useXAIExplanations();

  // Effet pour synchroniser les états
  useEffect(() => {
    setIsListening(voiceListening);
    setIsSpeaking(speaking);
  }, [voiceListening, speaking]);

  // Effet pour auto-scroll des messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  // Effet pour traitement des transcripts
  useEffect(() => {
    if (transcript && confidence > 0.7) {
      setCurrentMessage(transcript);
    }
  }, [transcript, confidence]);

  // Gestion des commandes vocales
  const handleVoiceCommand = useCallback(async (command: VoiceCommand) => {
    setIsProcessing(true);
    
    try {
      switch (command.type) {
        case 'query':
          await handleSendMessage(command.text);
          break;
        case 'control':
          await executeSystemCommand(command);
          break;
        case 'navigation':
          await handleNavigation(command);
          break;
        default:
          await handleSendMessage(command.text);
      }
    } catch (error) {
      console.error('Erreur commande vocale:', error);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  // Envoi de message
  const handleSendMessage = useCallback(async (message?: string) => {
    const messageText = message || currentMessage;
    if (!messageText.trim()) return;

    const userMessage: ConversationMessage = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
      language,
    };

    setConversation(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsProcessing(true);

    try {
      // Enrichissement du contexte avec données temps réel
      const enrichedContext = {
        ...initialContext,
        currentSensors: sensors?.length || 0,
        activeSensors: sensors?.filter(s => s.status === 'online').length || 0,
        anomalies: sensors?.filter(s => s.hasAnomaly).length || 0,
        lastExplanation: explanation,
        metrics,
        timestamp: new Date().toISOString(),
      };

      const response = await sendMessage(messageText, enrichedContext);

      const aiMessage: ConversationMessage = {
        id: (Date.now() + 1).toString(),
        text: response.text,
        sender: 'ai',
        timestamp: new Date(),
        language,
        confidence: response.confidence,
        provider: selectedAI,
        context: response.context,
        suggestions: response.suggestions,
        actions: response.actions,
      };

      setConversation(prev => [...prev, aiMessage]);

      // Synthèse vocale automatique si activée
      if (autoSpeak && voiceEnabled) {
        await speak(response.text);
      }

    } catch (error) {
      console.error('Erreur envoi message:', error);
      const errorMessage: ConversationMessage = {
        id: (Date.now() + 2).toString(),
        text: `Désolé, une erreur s'est produite: ${error.message}`,
        sender: 'ai',
        timestamp: new Date(),
        language,
        isError: true,
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  }, [currentMessage, language, selectedAI, autoSpeak, voiceEnabled, sensors, metrics, explanation, initialContext, sendMessage, speak]);

  // Exécution commandes système
  const executeSystemCommand = async (command: VoiceCommand) => {
    // Implémentation des commandes système (pause, play, navigation, etc.)
    console.log('Commande système:', command);
  };

  // Navigation
  const handleNavigation = async (command: VoiceCommand) => {
    // Implémentation navigation (dashboard, XAI, digital twin, etc.)
    console.log('Navigation:', command);
  };

  // Gestion micro
  const handleMicToggle = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Nettoyage conversation
  const handleClearConversation = () => {
    setConversation([]);
    clearConversation();
    resetTranscript();
  };

  // Messages d'accueil selon l'IA sélectionnée
  const getWelcomeMessage = () => {
    const messages = {
      gemini: `Bonjour ! Je suis votre assistant IA Google Gemini pour la Station Traffeyère. Je peux vous expliquer les analyses IoT, les anomalies détectées, et répondre à vos questions sur le système. Comment puis-je vous aider ?`,
      claude: `Salut ! Claude d'Anthropic à votre service pour la Station Traffeyère. Je suis spécialisé dans l'analyse des données IoT et l'explication des décisions IA. Que souhaitez-vous savoir ?`,
      gpt4: `Bonjour ! GPT-4 d'OpenAI pour vous assister sur la Station Traffeyère. Je peux analyser les données de vos 127 capteurs, expliquer les anomalies, et vous guider dans l'utilisation du système.`,
      perplexity: `Hello ! Perplexity AI pour la Station Traffeyère. Je combine recherche en temps réel et analyse IA pour vous donner les meilleures réponses sur votre infrastructure IoT.`,
    };
    return messages[selectedAI] || messages.gemini;
  };

  // Interface utilisateur si non supporté
  if (!voiceSupported) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        La reconnaissance vocale n'est pas supportée par votre navigateur.
        Veuillez utiliser Chrome, Firefox ou Safari récent.
      </Alert>
    );
  }

  return (
    <Dialog 
      open={isOpen} 
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { 
          height: '90vh',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }
      }}
    >
      {/* Header */}
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
              <SmartToy />
            </Avatar>
            <Box>
              <Typography variant="h6">
                Assistant IA Conversationnel - Station Traffeyère
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                <Chip 
                  size="small" 
                  label={selectedAI.toUpperCase()} 
                  color="secondary"
                  icon={<Psychology />}
                />
                <Chip 
                  size="small" 
                  label={language.toUpperCase()} 
                  color="info"
                  icon={<Translate />}
                />
                <Chip 
                  size="small" 
                  label={voiceEnabled ? 'Vocal ON' : 'Vocal OFF'} 
                  color={voiceEnabled ? 'success' : 'default'}
                  icon={voiceEnabled ? <VolumeUp /> : <VolumeOff />}
                />
              </Box>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Historique">
              <IconButton onClick={() => setShowHistory(true)} sx={{ color: 'white' }}>
                <History />
              </IconButton>
            </Tooltip>
            <Tooltip title="Paramètres">
              <IconButton onClick={() => setShowSettings(true)} sx={{ color: 'white' }}>
                <Settings />
              </IconButton>
            </Tooltip>
            <Tooltip title="Effacer conversation">
              <IconButton onClick={handleClearConversation} sx={{ color: 'white' }}>
                <Clear />
              </IconButton>
            </Tooltip>
            {onClose && (
              <Tooltip title="Fermer">
                <IconButton onClick={onClose} sx={{ color: 'white' }}>
                  <Close />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </DialogTitle>

      {/* Zone de conversation */}
      <DialogContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {/* Message d'accueil */}
          {conversation.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <MessageBubble isUser={false}>
                <CardContent>
                  <Typography variant="body1">
                    {getWelcomeMessage()}
                  </Typography>
                  <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip 
                      size="small" 
                      label="État capteurs IoT" 
                      variant="outlined" 
                      sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
                    />
                    <Chip 
                      size="small" 
                      label="Anomalies détectées" 
                      variant="outlined" 
                      sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
                    />
                    <Chip 
                      size="small" 
                      label="Performance IA" 
                      variant="outlined" 
                      sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
                    />
                  </Box>
                </CardContent>
              </MessageBubble>
            </motion.div>
          )}

          {/* Messages de conversation */}
          <AnimatePresence>
            {conversation.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <MessageBubble isUser={message.sender === 'user'}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>
                        {message.sender === 'user' ? 'U' : 'AI'}
                      </Avatar>
                      <Typography variant="caption">
                        {message.timestamp.toLocaleTimeString()}
                      </Typography>
                      {message.confidence && (
                        <Chip 
                          size="small" 
                          label={`${Math.round(message.confidence * 100)}%`} 
                          sx={{ height: 20, fontSize: 10 }}
                        />
                      )}
                    </Box>
                    <Typography variant="body1">
                      {message.text}
                    </Typography>
                    
                    {/* Actions suggérées */}
                    {message.actions && message.actions.length > 0 && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {message.actions.map((action, index) => (
                          <Button
                            key={index}
                            size="small"
                            variant="outlined"
                            sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
                            onClick={() => handleSendMessage(action)}
                          >
                            {action}
                          </Button>
                        ))}
                      </Box>
                    )}
                  </CardContent>
                </MessageBubble>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Indicateur de traitement */}
          {(isProcessing || aiLoading) && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, my: 2 }}>
              <LinearProgress sx={{ flex: 1 }} />
              <Typography variant="body2">
                {selectedAI.charAt(0).toUpperCase() + selectedAI.slice(1)} réfléchit...
              </Typography>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Zone de saisie et contrôles */}
        <Paper 
          sx={{ 
            p: 2, 
            m: 2, 
            bgcolor: 'rgba(255,255,255,0.1)', 
            backdropFilter: 'blur(10px)',
            borderRadius: 2,
          }}
        >
          {/* Visualisation audio */}
          {isListening && (
            <AudioWaveform amplitude={audioLevel}>
              {[...Array(8)].map((_, i) => (
                <div
                  key={i}
                  className="wave-bar"
                  style={{
                    height: `${Math.random() * 30 + 10}px`,
                  }}
                />
              ))}
            </AudioWaveform>
          )}

          {/* Transcript temps réel */}
          {transcript && (
            <Typography 
              variant="body2" 
              sx={{ 
                mb: 1, 
                p: 1, 
                bgcolor: 'rgba(255,255,255,0.1)', 
                borderRadius: 1,
                fontStyle: 'italic',
              }}
            >
              "{transcript}" {confidence && `(${Math.round(confidence * 100)}%)`}
            </Typography>
          )}

          {/* Contrôles principaux */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <VoiceButton
              isListening={isListening}
              onClick={handleMicToggle}
              disabled={!voiceEnabled}
              size="medium"
            >
              {isListening ? <Pause /> : <Mic />}
            </VoiceButton>

            <Box sx={{ flex: 1 }}>
              <input
                ref={inputRef}
                type="text"
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder={
                  isListening 
                    ? "Parlez maintenant..." 
                    : "Tapez votre message ou utilisez le micro..."
                }
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: 'none',
                  borderRadius: '24px',
                  background: 'rgba(255,255,255,0.9)',
                  fontSize: '14px',
                  outline: 'none',
                }}
                disabled={isListening}
              />
            </Box>

            <IconButton
              onClick={() => handleSendMessage()}
              disabled={!currentMessage.trim() || isProcessing}
              sx={{ 
                bgcolor: 'rgba(255,255,255,0.2)', 
                color: 'white',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
              }}
            >
              <Send />
            </IconButton>

            <IconButton
              onClick={() => setVoiceEnabled(!voiceEnabled)}
              sx={{ 
                color: voiceEnabled ? 'white' : 'rgba(255,255,255,0.5)',
              }}
            >
              {voiceEnabled ? <VolumeUp /> : <VolumeOff />}
            </IconButton>
          </Box>
        </Paper>
      </DialogContent>

      {/* Dialog Paramètres */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Paramètres Assistant IA</DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Sélection IA */}
            <FormControl fullWidth>
              <InputLabel>Modèle IA</InputLabel>
              <Select
                value={selectedAI}
                label="Modèle IA"
                onChange={(e) => {
                  setSelectedAI(e.target.value as AIProvider);
                  setProvider(e.target.value as AIProvider);
                }}
              >
                <MenuItem value="gemini">Google Gemini Pro</MenuItem>
                <MenuItem value="claude">Anthropic Claude</MenuItem>
                <MenuItem value="gpt4">OpenAI GPT-4</MenuItem>
                <MenuItem value="perplexity">Perplexity AI</MenuItem>
              </Select>
            </FormControl>

            {/* Langue */}
            <FormControl fullWidth>
              <InputLabel>Langue</InputLabel>
              <Select
                value={language}
                label="Langue"
                onChange={(e) => setLanguage(e.target.value as 'fr' | 'en')}
              >
                <MenuItem value="fr">Français</MenuItem>
                <MenuItem value="en">English</MenuItem>
              </Select>
            </FormControl>

            {/* Vitesse de parole */}
            <Box>
              <Typography gutterBottom>Vitesse de parole</Typography>
              <Slider
                value={speechRate}
                onChange={(_, value) => setSpeechRate(value as number)}
                min={0.5}
                max={2.0}
                step={0.1}
                marks={[
                  { value: 0.5, label: 'Lent' },
                  { value: 1.0, label: 'Normal' },
                  { value: 2.0, label: 'Rapide' },
                ]}
              />
            </Box>

            {/* Options */}
            <FormControlLabel
              control={
                <Switch
                  checked={autoSpeak}
                  onChange={(e) => setAutoSpeak(e.target.checked)}
                />
              }
              label="Lecture automatique des réponses"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={voiceEnabled}
                  onChange={(e) => setVoiceEnabled(e.target.checked)}
                />
              }
              label="Reconnaissance vocale activée"
            />
          </Box>
        </DialogContent>
      </Dialog>

      {/* Dialog Historique */}
      <Dialog open={showHistory} onClose={() => setShowHistory(false)} maxWidth="md" fullWidth>
        <DialogTitle>Historique des Conversations</DialogTitle>
        <DialogContent>
          <ConversationHistory
            conversations={conversation}
            onSelectMessage={(message) => setCurrentMessage(message.text)}
          />
        </DialogContent>
      </Dialog>
    </Dialog>
  );
};

export default ConversationalInterface;