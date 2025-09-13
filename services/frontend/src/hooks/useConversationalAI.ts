import { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';
import { ConversationMessage, AIProvider, ConversationContext, AIResponse } from '@types/conversation.types';

interface UseConversationalAIOptions {
  provider: AIProvider;
  expertiseLevel: 'novice' | 'intermediate' | 'expert' | 'researcher';
  context?: ConversationContext;
  maxTokens?: number;
  temperature?: number;
}

interface AIProviderConfig {
  baseURL: string;
  model: string;
  apiKey?: string;
  headers: Record<string, string>;
  formatMessage: (message: string, context: any) => any;
  parseResponse: (response: any) => AIResponse;
}

export const useConversationalAI = (options: UseConversationalAIOptions) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [currentProvider, setCurrentProvider] = useState<AIProvider>(options.provider);
  const [contextData, setContextData] = useState<any>(options.context);
  
  const conversationHistoryRef = useRef<ConversationMessage[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Configuration des providers IA
  const getProviderConfig = (provider: AIProvider): AIProviderConfig => {
    const configs: Record<AIProvider, AIProviderConfig> = {
      gemini: {
        baseURL: process.env.REACT_APP_GEMINI_API_URL || 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
        model: 'gemini-pro',
        headers: {
          'Content-Type': 'application/json',
        },
        formatMessage: (message: string, context: any) => ({
          contents: [{
            parts: [{
              text: `Tu es un assistant IA expert pour la Station Traffeyère, une station d'épuration d'eau avec 127 capteurs IoT et un système d'IA Edge.

Contexte technique actuel:
- Capteurs actifs: ${context?.activeSensors || 0}/${context?.currentSensors || 127}
- Anomalies détectées: ${context?.anomalies || 0}
- Performance IA Edge: ${context?.metrics?.edgeAI?.averageLatency || 0.28}ms
- Niveau utilisateur: ${options.expertiseLevel}
- Timestamp: ${context?.timestamp || new Date().toISOString()}

${context?.lastExplanation ? `
Dernière explication XAI:
- Confiance: ${Math.round((context.lastExplanation.confidence || 0) * 100)}%
- Méthode: ${context.lastExplanation.method || 'SHAP'}
- Temps traitement: ${context.lastExplanation.processingTime || 0}ms
` : ''}

Consignes:
- Réponds en français clair et précis
- Adapte ton niveau selon l'expertise: ${options.expertiseLevel}
- Concentre-toi sur les aspects IoT, IA et monitoring
- Propose des actions concrètes quand pertinent
- Reste dans le contexte de la station d'épuration

Question utilisateur: ${message}`
            }]
          }],
          generationConfig: {
            temperature: options.temperature || 0.7,
            candidateCount: 1,
            maxOutputTokens: options.maxTokens || 1000,
          }
        }),
        parseResponse: (response: any): AIResponse => ({
          text: response.candidates?.[0]?.content?.parts?.[0]?.text || 'Réponse non disponible',
          confidence: 0.9, // Gemini ne fournit pas de score de confiance explicite
          provider: 'gemini',
          context: response.candidates?.[0]?.safetyRatings,
          suggestions: [],
          actions: extractActions(response.candidates?.[0]?.content?.parts?.[0]?.text || ''),
        }),
      },

      claude: {
        baseURL: process.env.REACT_APP_CLAUDE_API_URL || 'https://api.anthropic.com/v1/messages',
        model: 'claude-3-sonnet-20240229',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': process.env.REACT_APP_CLAUDE_API_KEY || '',
          'anthropic-version': '2023-06-01',
        },
        formatMessage: (message: string, context: any) => ({
          model: 'claude-3-sonnet-20240229',
          max_tokens: options.maxTokens || 1000,
          temperature: options.temperature || 0.7,
          system: `Tu es Claude, assistant IA expert pour la Station Traffeyère IoT/IA. 

Tu disposes des données temps réel:
- ${context?.activeSensors || 0} capteurs actifs sur ${context?.currentSensors || 127}
- ${context?.anomalies || 0} anomalies détectées
- Performance IA: ${context?.metrics?.edgeAI?.averageLatency || 0.28}ms
- Utilisateur niveau: ${options.expertiseLevel}

Ton rôle: analyser, expliquer et conseiller sur l'infrastructure IoT avec précision technique adaptée au niveau utilisateur.`,
          messages: [{
            role: 'user',
            content: message
          }]
        }),
        parseResponse: (response: any): AIResponse => ({
          text: response.content?.[0]?.text || 'Réponse non disponible',
          confidence: 0.95, // Claude est généralement très fiable
          provider: 'claude',
          context: response.usage,
          suggestions: [],
          actions: extractActions(response.content?.[0]?.text || ''),
        }),
      },

      gpt4: {
        baseURL: process.env.REACT_APP_OPENAI_API_URL || 'https://api.openai.com/v1/chat/completions',
        model: 'gpt-4-turbo-preview',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.REACT_APP_OPENAI_API_KEY || ''}`,
        },
        formatMessage: (message: string, context: any) => ({
          model: 'gpt-4-turbo-preview',
          messages: [
            {
              role: 'system',
              content: `Tu es un assistant IA GPT-4 expert pour la Station Traffeyère, infrastructure critique IoT/IA.

État système temps réel:
- Capteurs: ${context?.activeSensors || 0}/${context?.currentSensors || 127} actifs
- Anomalies: ${context?.anomalies || 0}
- Latence IA: ${context?.metrics?.edgeAI?.averageLatency || 0.28}ms (objectif <1ms)
- Niveau utilisateur: ${options.expertiseLevel}

Mission: assistance experte IoT/IA avec explications adaptées au niveau technique de l'utilisateur. Focus sur analyse de données, détection d'anomalies, et optimisation performance.`
            },
            {
              role: 'user',
              content: message
            }
          ],
          temperature: options.temperature || 0.7,
          max_tokens: options.maxTokens || 1000,
          top_p: 1,
          frequency_penalty: 0,
          presence_penalty: 0,
        }),
        parseResponse: (response: any): AIResponse => ({
          text: response.choices?.[0]?.message?.content || 'Réponse non disponible',
          confidence: response.choices?.[0]?.finish_reason === 'stop' ? 0.9 : 0.7,
          provider: 'gpt4',
          context: response.usage,
          suggestions: [],
          actions: extractActions(response.choices?.[0]?.message?.content || ''),
        }),
      },

      perplexity: {
        baseURL: process.env.REACT_APP_PERPLEXITY_API_URL || 'https://api.perplexity.ai/chat/completions',
        model: 'llama-3.1-sonar-large-128k-online',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.REACT_APP_PERPLEXITY_API_KEY || ''}',
        },
        formatMessage: (message: string, context: any) => ({
          model: 'llama-3.1-sonar-large-128k-online',
          messages: [
            {
              role: 'system',
              content: `Assistant IA Perplexity pour Station Traffeyère IoT/IA. Combine recherche temps réel + analyse données système.

Données actuelles:
- Infrastructure: ${context?.currentSensors || 127} capteurs IoT
- État: ${context?.activeSensors || 0} actifs, ${context?.anomalies || 0} anomalies
- Performance: ${context?.metrics?.edgeAI?.averageLatency || 0.28}ms latence IA
- Utilisateur: ${options.expertiseLevel}

Capacités: recherche info récentes + analyse contexte technique + recommandations expertes.`
            },
            {
              role: 'user',
              content: message
            }
          ],
          temperature: options.temperature || 0.2, // Plus faible pour Perplexity
          max_tokens: options.maxTokens || 1000,
          top_p: 0.9,
          search_domain_filter: ['technical', 'industrial', 'iot'],
          return_citations: true,
        }),
        parseResponse: (response: any): AIResponse => ({
          text: response.choices?.[0]?.message?.content || 'Réponse non disponible',
          confidence: response.choices?.[0]?.finish_reason === 'stop' ? 0.85 : 0.7,
          provider: 'perplexity',
          context: response.usage,
          suggestions: [],
          actions: extractActions(response.choices?.[0]?.message?.content || ''),
          citations: response.citations, // Spécifique à Perplexity
        }),
      },
    };

    return configs[provider];
  };

  // Extraction d'actions suggérées à partir du texte
  const extractActions = (text: string): string[] => {
    const actions: string[] = [];
    
    // Patterns pour détecter les actions suggérées
    const actionPatterns = [
      /(?:vous pouvez|je recommande|il serait bien de|essayez de)\s+(.+?)(?:\.|,|$)/gi,
      /(?:action|étape|procédure)\s*:\s*(.+?)(?:\.|,|$)/gi,
      /(?:vérifiez|contrôlez|analysez|examinez)\s+(.+?)(?:\.|,|$)/gi,
    ];

    actionPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        const action = match[1]?.trim();
        if (action && action.length > 10 && action.length < 100) {
          actions.push(action);
        }
      }
    });

    return actions.slice(0, 3); // Limite à 3 actions
  };

  // Fonction d'envoi de message
  const sendMessage = useCallback(async (message: string, context?: any): Promise<AIResponse> => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setLoading(true);
    setError(null);

    try {
      const config = getProviderConfig(currentProvider);
      const enrichedContext = { ...contextData, ...context };
      
      // Préparation de la requête
      const requestData = config.formatMessage(message, enrichedContext);
      
      // Ajout de l'API key si nécessaire
      let headers = config.headers;
      if (currentProvider === 'gemini' && process.env.REACT_APP_GEMINI_API_KEY) {
        headers = {
          ...headers,
          'x-goog-api-key': process.env.REACT_APP_GEMINI_API_KEY,
        };
      }

      console.log(`📤 Envoi vers ${currentProvider.toUpperCase()}:`, {
        provider: currentProvider,
        message: message.substring(0, 100) + '...',
        context: {
          sensors: enrichedContext?.currentSensors,
          anomalies: enrichedContext?.anomalies,
          expertiseLevel: options.expertiseLevel,
        }
      });

      // Appel API avec gestion d'erreur et timeout
      const response = await axios({
        method: 'POST',
        url: config.baseURL,
        headers,
        data: requestData,
        timeout: 30000, // 30 secondes
        signal: abortControllerRef.current.signal,
      });

      console.log(`📥 Réponse ${currentProvider.toUpperCase()}:`, {
        status: response.status,
        dataKeys: Object.keys(response.data || {}),
      });

      // Parse de la réponse selon le provider
      const parsedResponse = config.parseResponse(response.data);
      
      // Mise à jour de l'historique
      const userMessage: ConversationMessage = {
        id: Date.now().toString(),
        text: message,
        sender: 'user',
        timestamp: new Date(),
        language: 'fr',
      };

      const aiMessage: ConversationMessage = {
        id: (Date.now() + 1).toString(),
        text: parsedResponse.text,
        sender: 'ai',
        timestamp: new Date(),
        language: 'fr',
        confidence: parsedResponse.confidence,
        provider: currentProvider,
        context: parsedResponse.context,
        suggestions: parsedResponse.suggestions,
        actions: parsedResponse.actions,
      };

      conversationHistoryRef.current = [...conversationHistoryRef.current, userMessage, aiMessage];
      setConversation([...conversationHistoryRef.current]);

      return parsedResponse;

    } catch (error: any) {
      console.error(`❌ Erreur ${currentProvider.toUpperCase()}:`, error);
      
      if (error.code === 'ECONNABORTED') {
        setError(new Error('Timeout: La requête a pris trop de temps'));
      } else if (error.response?.status === 429) {
        setError(new Error('Trop de requêtes: Veuillez patienter quelques secondes'));
      } else if (error.response?.status === 401) {
        setError(new Error('Erreur d\'authentification: Vérifiez les clés API'));
      } else if (error.response?.status === 402) {
        setError(new Error('Quota dépassé: Vérifiez votre abonnement API'));
      } else {
        setError(error);
      }

      // Fallback response en cas d'erreur
      return {
        text: `Désolé, je rencontre des difficultés techniques avec ${currentProvider}. Veuillez réessayer ou changer de modèle IA dans les paramètres.`,
        confidence: 0,
        provider: currentProvider,
        context: { error: error.message },
        suggestions: [],
        actions: ['Changer de modèle IA', 'Réessayer plus tard', 'Contacter le support'],
      };

    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [currentProvider, contextData, options.expertiseLevel, options.maxTokens, options.temperature]);

  // Changement de provider
  const setProvider = useCallback((provider: AIProvider) => {
    setCurrentProvider(provider);
    console.log(`🔄 Changement vers ${provider.toUpperCase()}`);
  }, []);

  // Nettoyage de la conversation
  const clearConversation = useCallback(() => {
    conversationHistoryRef.current = [];
    setConversation([]);
    console.log('🧹 Conversation effacée');
  }, []);

  // Mise à jour du contexte
  const updateContext = useCallback((newContext: Partial<ConversationContext>) => {
    setContextData(prev => ({ ...prev, ...newContext }));
  }, []);

  // Annulation de la requête en cours
  const cancelRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
    }
  }, []);

  // Nettoyage au démontage
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Validation des clés API (côté client pour debug uniquement)
  const validateAPIKeys = useCallback(() => {
    const keys = {
      gemini: !!process.env.REACT_APP_GEMINI_API_KEY,
      claude: !!process.env.REACT_APP_CLAUDE_API_KEY,
      gpt4: !!process.env.REACT_APP_OPENAI_API_KEY,
      perplexity: !!process.env.REACT_APP_PERPLEXITY_API_KEY,
    };

    console.log('🔑 État des clés API:', keys);
    return keys;
  }, []);

  return {
    // Actions principales
    sendMessage,
    setProvider,
    clearConversation,
    updateContext,
    cancelRequest,
    validateAPIKeys,

    // État
    loading,
    error,
    conversation,
    currentProvider,
    contextData,

    // Configuration
    supportedProviders: ['gemini', 'claude', 'gpt4', 'perplexity'] as AIProvider[],
    expertiseLevel: options.expertiseLevel,
  };
};

export default useConversationalAI;