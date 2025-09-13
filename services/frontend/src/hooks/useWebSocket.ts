import { useState, useEffect, useRef, useCallback } from 'react';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  protocols?: string | string[];
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onReconnect?: (attempt: number) => void;
  onMaxReconnectAttemptsReached?: () => void;
}

interface WebSocketMessage {
  id: string;
  timestamp: number;
  data: any;
  type?: string;
}

export const useWebSocket = (url: string | null, options: UseWebSocketOptions = {}) => {
  const {
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    protocols,
    onOpen,
    onMessage,
    onClose,
    onError,
    onReconnect,
    onMaxReconnectAttemptsReached,
  } = options;

  // État principal
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [messageHistory, setMessageHistory] = useState<WebSocketMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Références
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);
  const messageIdCounter = useRef(0);

  // Nettoyage des timeouts
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Configuration du heartbeat
  const setupHeartbeat = useCallback(() => {
    if (heartbeatInterval > 0 && ws.current?.readyState === WebSocket.OPEN) {
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
          console.log('🔄 WebSocket heartbeat envoyé');
        }
      }, heartbeatInterval);
    }
  }, [heartbeatInterval]);

  // Génération d'ID unique pour les messages
  const generateMessageId = useCallback(() => {
    messageIdCounter.current += 1;
    return `msg-${Date.now()}-${messageIdCounter.current}`;
  }, []);

  // Traitement des messages entrants
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      let messageData;
      try {
        messageData = JSON.parse(event.data);
      } catch {
        messageData = event.data;
      }

      // Ignorer les messages de type pong
      if (messageData?.type === 'pong') {
        console.log('🔄 WebSocket pong reçu');
        return;
      }

      const message: WebSocketMessage = {
        id: generateMessageId(),
        timestamp: Date.now(),
        data: messageData,
        type: messageData?.type || 'data',
      };

      if (isMountedRef.current) {
        setLastMessage(message);
        setMessageHistory(prev => {
          const newHistory = [...prev, message];
          // Garder seulement les 100 derniers messages
          return newHistory.slice(-100);
        });
      }

      onMessage?.(event);
      console.log('📨 WebSocket message reçu:', message);

    } catch (error: any) {
      console.error('❌ Erreur traitement message WebSocket:', error);
      setError(`Erreur traitement message: ${error.message}`);
    }
  }, [generateMessageId, onMessage]);

  // Connexion WebSocket
  const connect = useCallback(() => {
    if (!url || !isMountedRef.current) {
      return;
    }

    if (ws.current?.readyState === WebSocket.OPEN || ws.current?.readyState === WebSocket.CONNECTING) {
      console.log('🔗 WebSocket déjà connecté ou en cours de connexion');
      return;
    }

    setStatus('connecting');
    setError(null);
    console.log('🔗 Connexion WebSocket à:', url);

    try {
      ws.current = new WebSocket(url, protocols);

      ws.current.onopen = (event) => {
        if (!isMountedRef.current) return;

        console.log('✅ WebSocket connecté');
        setStatus('connected');
        setError(null);
        setReconnectAttempts(0);
        setupHeartbeat();
        onOpen?.(event);
      };

      ws.current.onmessage = handleMessage;

      ws.current.onclose = (event) => {
        if (!isMountedRef.current) return;

        console.log('🔌 WebSocket fermé:', event.code, event.reason);
        setStatus('disconnected');
        clearTimeouts();

        onClose?.(event);

        // Tentative de reconnexion si activée et pas de fermeture intentionnelle
        if (reconnect && event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          const nextAttempt = reconnectAttempts + 1;
          setReconnectAttempts(nextAttempt);

          console.log(`🔄 Tentative de reconnexion ${nextAttempt}/${maxReconnectAttempts} dans ${reconnectInterval}ms`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              onReconnect?.(nextAttempt);
              connect();
            }
          }, reconnectInterval);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.log('❌ Nombre maximum de tentatives de reconnexion atteint');
          onMaxReconnectAttemptsReached?.();
        }
      };

      ws.current.onerror = (event) => {
        if (!isMountedRef.current) return;

        console.error('❌ Erreur WebSocket:', event);
        setStatus('error');
        setError('Erreur de connexion WebSocket');
        onError?.(event);
      };

    } catch (error: any) {
      console.error('❌ Erreur création WebSocket:', error);
      setStatus('error');
      setError(`Erreur création WebSocket: ${error.message}`);
    }
  }, [
    url,
    protocols,
    reconnect,
    reconnectInterval,
    maxReconnectAttempts,
    reconnectAttempts,
    setupHeartbeat,
    handleMessage,
    onOpen,
    onClose,
    onError,
    onReconnect,
    onMaxReconnectAttemptsReached,
  ]);

  // Déconnexion WebSocket
  const disconnect = useCallback((code = 1000, reason = 'Disconnection requested') => {
    if (ws.current) {
      ws.current.close(code, reason);
    }
    clearTimeouts();
    setStatus('disconnected');
    setReconnectAttempts(0);
    console.log('🔌 WebSocket déconnecté manuellement');
  }, [clearTimeouts]);

  // Envoi de message
  const sendMessage = useCallback((data: any, type?: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ WebSocket non connecté, message non envoyé');
      return false;
    }

    try {
      const messageToSend = typeof data === 'string' ? data : JSON.stringify({
        type: type || 'data',
        data,
        timestamp: Date.now(),
      });

      ws.current.send(messageToSend);
      console.log('📤 Message WebSocket envoyé:', { type, dataSize: messageToSend.length });
      return true;
    } catch (error: any) {
      console.error('❌ Erreur envoi message WebSocket:', error);
      setError(`Erreur envoi message: ${error.message}`);
      return false;
    }
  }, []);

  // Réinitialisation des tentatives de reconnexion
  const resetReconnectAttempts = useCallback(() => {
    setReconnectAttempts(0);
  }, []);

  // Obtenir l'historique filtré par type
  const getMessagesByType = useCallback((type: string) => {
    return messageHistory.filter(message => message.type === type);
  }, [messageHistory]);

  // Obtenir les derniers messages
  const getRecentMessages = useCallback((count: number = 10) => {
    return messageHistory.slice(-count);
  }, [messageHistory]);

  // Nettoyer l'historique des messages
  const clearMessageHistory = useCallback(() => {
    setMessageHistory([]);
    setLastMessage(null);
  }, []);

  // Obtenir les statistiques de connexion
  const getConnectionStats = useCallback(() => {
    return {
      status,
      reconnectAttempts,
      maxReconnectAttempts,
      messageCount: messageHistory.length,
      lastMessageTime: lastMessage?.timestamp || null,
      isConnected: status === 'connected',
      canReconnect: reconnect && reconnectAttempts < maxReconnectAttempts,
    };
  }, [status, reconnectAttempts, maxReconnectAttempts, messageHistory.length, lastMessage, reconnect]);

  // Effet principal de connexion
  useEffect(() => {
    isMountedRef.current = true;

    if (url) {
      connect();
    }

    return () => {
      isMountedRef.current = false;
      clearTimeouts();
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [url]); // Seulement quand l'URL change

  // Nettoyage au démontage
  useEffect(() => {
    return () => {
      clearTimeouts();
      if (ws.current) {
        ws.current.close(1000, 'Component unmounting');
      }
    };
  }, [clearTimeouts]);

  return {
    // État de connexion
    status,
    error,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    reconnectAttempts,

    // Données
    lastMessage,
    messageHistory,

    // Actions de connexion
    connect,
    disconnect,
    sendMessage,
    resetReconnectAttempts,

    // Utilitaires pour les messages
    getMessagesByType,
    getRecentMessages,
    clearMessageHistory,

    // Statistiques
    getConnectionStats,

    // Configuration actuelle
    config: {
      url,
      reconnect,
      reconnectInterval,
      maxReconnectAttempts,
      heartbeatInterval,
    },

    // Informations de statut
    statusInfo: {
      readyState: ws.current?.readyState || WebSocket.CLOSED,
      readyStateText: ws.current ? 
        ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][ws.current.readyState] || 'UNKNOWN' : 
        'NOT_INITIALIZED',
    },
  };
};

export default useWebSocket;