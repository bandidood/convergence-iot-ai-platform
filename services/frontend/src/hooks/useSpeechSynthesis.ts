import { useState, useEffect, useRef, useCallback } from 'react';

interface UseSpeechSynthesisOptions {
  rate?: number;
  pitch?: number;
  volume?: number;
  lang?: string;
  voice?: SpeechSynthesisVoice | null;
}

interface SpeechQueueItem {
  id: string;
  text: string;
  options: UseSpeechSynthesisOptions;
  utterance: SpeechSynthesisUtterance;
}

export const useSpeechSynthesis = (options: UseSpeechSynthesisOptions = {}) => {
  const [isSupported, setIsSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [pending, setPending] = useState(false);
  const [paused, setPaused] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [currentText, setCurrentText] = useState('');
  const [error, setError] = useState<string | null>(null);

  const speechQueue = useRef<SpeechQueueItem[]>([]);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const isInitializedRef = useRef(false);

  const {
    rate = 1.0,
    pitch = 1.0,
    volume = 0.8,
    lang = 'fr-FR',
    voice = null,
  } = options;

  // Vérification du support et initialisation
  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setIsSupported(false);
      console.warn('🔊 Speech Synthesis API non supportée par ce navigateur');
      return;
    }

    setIsSupported(true);
    loadVoices();

    // Écouter les changements de voix (certains navigateurs chargent les voix de façon asynchrone)
    const handleVoicesChanged = () => {
      loadVoices();
    };

    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = handleVoicesChanged;
    }

    // Nettoyage au démontage
    return () => {
      if (speechSynthesis.speaking) {
        speechSynthesis.cancel();
      }
      if (speechSynthesis.onvoiceschanged) {
        speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  // Chargement des voix disponibles
  const loadVoices = useCallback(() => {
    const availableVoices = speechSynthesis.getVoices();
    setVoices(availableVoices);

    // Sélection automatique d'une voix française si disponible
    if (!selectedVoice && availableVoices.length > 0) {
      const frenchVoice = availableVoices.find(v => 
        v.lang.startsWith('fr') && v.default
      ) || availableVoices.find(v => v.lang.startsWith('fr')) || availableVoices[0];

      setSelectedVoice(frenchVoice);
      console.log('🔊 Voix sélectionnée:', frenchVoice?.name, frenchVoice?.lang);
    }

    if (!isInitializedRef.current && availableVoices.length > 0) {
      isInitializedRef.current = true;
      console.log('🔊 Speech Synthesis initialisé avec', availableVoices.length, 'voix disponibles');
    }
  }, [selectedVoice]);

  // Fonction pour créer une utterance
  const createUtterance = useCallback((text: string, customOptions?: Partial<UseSpeechSynthesisOptions>) => {
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configuration des paramètres
    utterance.rate = customOptions?.rate ?? rate;
    utterance.pitch = customOptions?.pitch ?? pitch;
    utterance.volume = customOptions?.volume ?? volume;
    utterance.lang = customOptions?.lang ?? lang;
    utterance.voice = customOptions?.voice ?? selectedVoice ?? voice;

    return utterance;
  }, [rate, pitch, volume, lang, selectedVoice, voice]);

  // Gestion des événements utterance
  const setupUtteranceEvents = useCallback((
    utterance: SpeechSynthesisUtterance, 
    id: string,
    onComplete?: () => void
  ) => {
    utterance.onstart = () => {
      console.log('🔊 Synthèse vocale démarrée:', id);
      setSpeaking(true);
      setPending(false);
      setError(null);
    };

    utterance.onend = () => {
      console.log('🔊 Synthèse vocale terminée:', id);
      setSpeaking(false);
      setCurrentText('');
      currentUtteranceRef.current = null;
      
      // Traitement du prochain élément dans la queue
      processQueue();
      onComplete?.();
    };

    utterance.onerror = (event) => {
      console.error('🔊 Erreur synthèse vocale:', event.error, event.name);
      setSpeaking(false);
      setPending(false);
      setError(`Erreur synthèse vocale: ${event.error}`);
      
      // Continuer avec le prochain élément malgré l'erreur
      processQueue();
    };

    utterance.onpause = () => {
      console.log('🔊 Synthèse vocale en pause:', id);
      setPaused(true);
    };

    utterance.onresume = () => {
      console.log('🔊 Synthèse vocale reprise:', id);
      setPaused(false);
    };

    utterance.onboundary = (event) => {
      // Événement déclenché à chaque mot/phrase (optionnel pour feedback visuel)
      if (event.name === 'word') {
        const spokenText = utterance.text.substring(0, event.charIndex);
        // Peut être utilisé pour surligner le texte en cours de lecture
      }
    };
  }, []);

  // Traitement de la queue de synthèse
  const processQueue = useCallback(() => {
    if (speechQueue.current.length === 0 || speaking) {
      return;
    }

    const nextItem = speechQueue.current.shift();
    if (nextItem) {
      setCurrentText(nextItem.text);
      currentUtteranceRef.current = nextItem.utterance;
      speechSynthesis.speak(nextItem.utterance);
    }
  }, [speaking]);

  // Fonction principale pour parler
  const speak = useCallback((
    text: string, 
    customOptions?: Partial<UseSpeechSynthesisOptions>,
    priority: 'high' | 'normal' = 'normal'
  ): Promise<void> => {
    if (!isSupported || !text.trim()) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        const utterance = createUtterance(text, customOptions);
        const id = Date.now().toString();

        setupUtteranceEvents(utterance, id, () => resolve());

        const queueItem: SpeechQueueItem = {
          id,
          text: text.trim(),
          options: { ...options, ...customOptions },
          utterance,
        };

        // Gestion de la priorité
        if (priority === 'high') {
          // Arrêter la synthèse actuelle et placer en tête de queue
          if (speaking) {
            speechSynthesis.cancel();
          }
          speechQueue.current.unshift(queueItem);
        } else {
          speechQueue.current.push(queueItem);
        }

        setPending(speechQueue.current.length > 0);
        
        // Démarrer le traitement si pas de synthèse en cours
        if (!speaking) {
          processQueue();
        }

        console.log('🔊 Ajouté à la queue de synthèse:', { id, priority, queueLength: speechQueue.current.length });

      } catch (error: any) {
        console.error('🔊 Erreur création utterance:', error);
        setError(`Erreur création utterance: ${error.message}`);
        reject(error);
      }
    });
  }, [isSupported, createUtterance, setupUtteranceEvents, speaking, processQueue, options]);

  // Arrêter la synthèse
  const stop = useCallback(() => {
    if (!isSupported) return;

    speechSynthesis.cancel();
    speechQueue.current = [];
    setSpeaking(false);
    setPending(false);
    setPaused(false);
    setCurrentText('');
    currentUtteranceRef.current = null;
    
    console.log('🔊 Synthèse vocale arrêtée et queue vidée');
  }, [isSupported]);

  // Mettre en pause
  const pause = useCallback(() => {
    if (!isSupported || !speaking) return;

    speechSynthesis.pause();
    console.log('🔊 Synthèse vocale mise en pause');
  }, [isSupported, speaking]);

  // Reprendre
  const resume = useCallback(() => {
    if (!isSupported || !paused) return;

    speechSynthesis.resume();
    console.log('🔊 Synthèse vocale reprise');
  }, [isSupported, paused]);

  // Sélectionner une voix
  const setVoice = useCallback((voice: SpeechSynthesisVoice) => {
    setSelectedVoice(voice);
    console.log('🔊 Voix changée:', voice.name, voice.lang);
  }, []);

  // Obtenir les voix filtrées par langue
  const getVoicesByLanguage = useCallback((language: string) => {
    return voices.filter(voice => voice.lang.startsWith(language));
  }, [voices]);

  // Obtenir la voix par défaut pour une langue
  const getDefaultVoiceForLanguage = useCallback((language: string) => {
    const languageVoices = getVoicesByLanguage(language);
    return languageVoices.find(voice => voice.default) || languageVoices[0] || null;
  }, [getVoicesByLanguage]);

  // Test de synthèse
  const testSpeech = useCallback(async (testText?: string) => {
    const text = testText || 'Test de synthèse vocale pour la Station Traffeyère';
    try {
      await speak(text, { rate: 1.2, pitch: 1.0, volume: 0.6 });
      return true;
    } catch (error) {
      console.error('🔊 Erreur test synthèse:', error);
      return false;
    }
  }, [speak]);

  // Obtenir les capacités de synthèse
  const getCapabilities = useCallback(() => {
    return {
      supported: isSupported,
      voicesCount: voices.length,
      selectedVoice: selectedVoice?.name || null,
      currentLanguage: selectedVoice?.lang || lang,
      supportedLanguages: [...new Set(voices.map(v => v.lang.split('-')[0]))],
      canPause: isSupported,
      canResume: isSupported,
      canCancel: isSupported,
    };
  }, [isSupported, voices, selectedVoice, lang]);

  // Parler des données IoT contextuelles
  const speakIoTData = useCallback(async (sensors: any[], anomalies: number) => {
    const activeSensors = sensors?.filter(s => s.status === 'online').length || 0;
    const totalSensors = sensors?.length || 0;
    
    let message = `État de la station Traffeyère: ${activeSensors} capteurs actifs sur ${totalSensors}.`;
    
    if (anomalies > 0) {
      message += ` Attention: ${anomalies} anomalie${anomalies > 1 ? 's détectées' : ' détectée'}.`;
    } else {
      message += ' Tous les systèmes fonctionnent normalement.';
    }

    await speak(message, { rate: 1.1, pitch: 1.1 });
  }, [speak]);

  // Annoncer une alerte
  const announceAlert = useCallback(async (alertMessage: string, severity: 'low' | 'medium' | 'high' = 'medium') => {
    const prefixes = {
      low: 'Information',
      medium: 'Attention',
      high: 'Alerte critique',
    };

    const rates = {
      low: 1.0,
      medium: 0.9,
      high: 0.8,
    };

    const pitches = {
      low: 1.0,
      medium: 1.2,
      high: 1.4,
    };

    const message = `${prefixes[severity]}: ${alertMessage}`;
    
    await speak(message, {
      rate: rates[severity],
      pitch: pitches[severity],
      volume: 0.9,
    }, severity === 'high' ? 'high' : 'normal');
  }, [speak]);

  return {
    // État principal
    isSupported,
    speaking,
    pending,
    paused,
    voices,
    selectedVoice,
    currentText,
    error,

    // Actions principales
    speak,
    stop,
    pause,
    resume,
    setVoice,

    // Utilitaires
    getVoicesByLanguage,
    getDefaultVoiceForLanguage,
    testSpeech,
    getCapabilities,
    speakIoTData,
    announceAlert,

    // Configuration actuelle
    config: {
      rate,
      pitch,
      volume,
      lang,
      voice: selectedVoice,
    },

    // Informations sur la queue
    queueInfo: {
      length: speechQueue.current.length,
      isEmpty: speechQueue.current.length === 0,
      currentIndex: currentUtteranceRef.current ? 0 : -1,
    },
  };
};

export default useSpeechSynthesis;