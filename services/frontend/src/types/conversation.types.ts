export type AIProvider = 'gemini' | 'claude' | 'gpt4' | 'perplexity';

export type VoiceCommandType = 'query' | 'control' | 'navigation' | 'system';

export type ConversationSender = 'user' | 'ai';

export type ConversationLanguage = 'fr' | 'en';

export interface ConversationMessage {
  id: string;
  text: string;
  sender: ConversationSender;
  timestamp: Date;
  language: ConversationLanguage;
  confidence?: number;
  provider?: AIProvider;
  context?: any;
  suggestions?: string[];
  actions?: string[];
  isError?: boolean;
  metadata?: {
    processingTime?: number;
    tokenCount?: number;
    cost?: number;
  };
}

export interface VoiceCommand {
  id: string;
  text: string;
  type: VoiceCommandType;
  confidence: number;
  timestamp: Date;
  language: ConversationLanguage;
  metadata?: {
    audioLevel?: number;
    duration?: number;
    recognized?: boolean;
  };
}

export interface ConversationContext {
  stationId?: string;
  userId?: string;
  sessionId?: string;
  currentSensors?: number;
  activeSensors?: number;
  anomalies?: number;
  lastExplanation?: any;
  metrics?: any;
  timestamp?: string;
  location?: {
    latitude?: number;
    longitude?: number;
    address?: string;
  };
  preferences?: {
    language: ConversationLanguage;
    expertiseLevel: 'novice' | 'intermediate' | 'expert' | 'researcher';
    voiceEnabled: boolean;
    autoSpeak: boolean;
  };
}

export interface AIResponse {
  text: string;
  confidence: number;
  provider: AIProvider;
  context?: any;
  suggestions?: string[];
  actions?: string[];
  metadata?: {
    processingTime: number;
    tokenCount?: number;
    cost?: number;
    model?: string;
  };
  error?: string;
}

export interface ConversationHistory {
  id: string;
  sessionId: string;
  messages: ConversationMessage[];
  startTime: Date;
  endTime?: Date;
  totalMessages: number;
  providers: AIProvider[];
  languages: ConversationLanguage[];
  metadata?: {
    averageResponseTime?: number;
    totalCost?: number;
    satisfaction?: number;
  };
}

export interface VoiceSettings {
  enabled: boolean;
  language: ConversationLanguage;
  recognition: {
    continuous: boolean;
    interimResults: boolean;
    maxAlternatives: number;
    sensitivity: number;
  };
  synthesis: {
    rate: number;
    pitch: number;
    volume: number;
    voice?: string;
  };
  commands: {
    enabled: boolean;
    customCommands: VoiceCommand[];
  };
}

export interface ConversationStats {
  totalConversations: number;
  totalMessages: number;
  averageSessionLength: number;
  mostUsedProvider: AIProvider;
  preferredLanguage: ConversationLanguage;
  averageConfidence: number;
  successRate: number;
  errorRate: number;
  responseTime: {
    average: number;
    p50: number;
    p95: number;
    p99: number;
  };
}

export interface ConversationError {
  id: string;
  type: 'network' | 'api' | 'voice' | 'parsing' | 'unknown';
  message: string;
  details?: any;
  timestamp: Date;
  provider?: AIProvider;
  recoverable: boolean;
  retryCount: number;
}

// Événements WebSocket pour la communication temps réel
export interface ConversationalWebSocketMessage {
  type: 'conversation' | 'voice' | 'system' | 'iot' | 'heartbeat';
  payload: {
    messageId?: string;
    sessionId?: string;
    data: any;
    timestamp: string;
  };
}

// Configuration des providers IA
export interface AIProviderConfig {
  name: AIProvider;
  displayName: string;
  baseURL: string;
  model: string;
  maxTokens: number;
  temperature: number;
  timeout: number;
  retryCount: number;
  rateLimiting: {
    requestsPerMinute: number;
    tokensPerMinute: number;
  };
  pricing: {
    inputTokens: number; // Prix par 1K tokens
    outputTokens: number;
  };
  supportedFeatures: string[];
  systemPrompt?: string;
  contextWindow: number;
}

// Hooks return types
export interface UseConversationalAIReturn {
  sendMessage: (text: string, context?: ConversationContext) => Promise<AIResponse>;
  loading: boolean;
  error: ConversationError | null;
  conversation: ConversationMessage[];
  currentProvider: AIProvider;
  setProvider: (provider: AIProvider) => void;
  clearConversation: () => void;
  contextData: ConversationContext;
  stats: ConversationStats;
}

export interface UseVoiceRecognitionReturn {
  isSupported: boolean;
  listening: boolean;
  transcript: string;
  interimTranscript: string;
  finalTranscript: string;
  confidence: number;
  error: string | null;
  start: () => void;
  stop: () => void;
  reset: () => void;
  testMicrophone: () => Promise<boolean>;
  getCapabilities: () => any;
}

export interface UseSpeechSynthesisReturn {
  isSupported: boolean;
  speaking: boolean;
  pending: boolean;
  paused: boolean;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  currentText: string;
  error: string | null;
  speak: (text: string, options?: any) => Promise<void>;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  setVoice: (voice: SpeechSynthesisVoice) => void;
  testSpeech: () => Promise<boolean>;
  announceAlert: (message: string, severity?: 'low' | 'medium' | 'high') => Promise<void>;
  speakIoTData: (sensors: any[], anomalies: number) => Promise<void>;
}

// Événements et callbacks
export interface ConversationalEventHandlers {
  onMessageSent?: (message: ConversationMessage) => void;
  onMessageReceived?: (message: ConversationMessage) => void;
  onVoiceStart?: () => void;
  onVoiceEnd?: (transcript: string) => void;
  onSpeechStart?: (text: string) => void;
  onSpeechEnd?: () => void;
  onError?: (error: ConversationError) => void;
  onProviderChange?: (provider: AIProvider) => void;
  onLanguageChange?: (language: ConversationLanguage) => void;
  onContextUpdate?: (context: ConversationContext) => void;
}

export default {
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
};