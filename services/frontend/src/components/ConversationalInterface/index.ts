// Composants principaux
export { default as ConversationalInterface } from './ConversationalInterface';
export { default as ConversationalInterfaceContainer } from './ConversationalInterfaceContainer';
export { default as ConversationalSettings } from './ConversationalSettings';

// Composants visuels
export { default as VoiceIndicator, ListeningIndicator, SpeakingIndicator, VoiceStatusBar } from './VoiceIndicator';

// Hooks conversationnels
export { useConversationalAI } from '../../hooks/useConversationalAI';
export { useVoiceRecognition } from '../../hooks/useVoiceRecognition';
export { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
export { useWebSocket } from '../../hooks/useWebSocket';

// Configuration
export {
  defaultConversationalConfig,
  systemPrompts,
  voiceCommands,
  automaticResponses,
  conversationalThemes,
  animationConfig,
  validateConfig,
  mergeConfig,
} from '../../config/conversationalConfig';

// Types
export type {
  AIProvider,
  VoiceCommandType,
  ConversationSender,
  ConversationLanguage,
  ConversationMessage,
  VoiceCommand,
  ConversationContext,
  AIResponse,
  ConversationHistory,
  VoiceSettings,
  ConversationStats,
  ConversationError,
  ConversationalWebSocketMessage,
  AIProviderConfig,
  UseConversationalAIReturn,
  UseVoiceRecognitionReturn,
  UseSpeechSynthesisReturn,
  ConversationalEventHandlers,
} from '../../types/conversation.types';

export type {
  ConversationalConfig,
  AIProviderConfig as ConfigAIProviderConfig,
  VoiceConfig,
} from '../../config/conversationalConfig';