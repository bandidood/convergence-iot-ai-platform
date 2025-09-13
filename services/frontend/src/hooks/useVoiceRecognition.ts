import { useState, useEffect, useRef, useCallback } from 'react';

interface UseVoiceRecognitionOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  serviceURI?: string;
  grammars?: any[];
}

interface VoiceRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
  alternatives: string[];
}

export const useVoiceRecognition = (options: UseVoiceRecognitionOptions = {}) => {
  const [isSupported, setIsSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isListeningRef = useRef(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    language = 'fr-FR',
    continuous = false,
    interimResults = true,
    maxAlternatives = 1,
    serviceURI,
    grammars = [],
  } = options;

  // Vérification du support navigateur
  useEffect(() => {
    const SpeechRecognition = 
      (window as any).SpeechRecognition || 
      (window as any).webkitSpeechRecognition ||
      (window as any).mozSpeechRecognition ||
      (window as any).msSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);
      initializeRecognition(SpeechRecognition);
    } else {
      setIsSupported(false);
      console.warn('🎤 Speech Recognition API non supportée par ce navigateur');
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [language, continuous, interimResults, maxAlternatives]);

  // Initialisation de SpeechRecognition
  const initializeRecognition = useCallback((SpeechRecognition: any) => {
    try {
      const recognition = new SpeechRecognition();

      // Configuration de base
      recognition.lang = language;
      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.maxAlternatives = maxAlternatives;

      // Configuration URI service (pour certains navigateurs)
      if (serviceURI) {
        recognition.serviceURI = serviceURI;
      }

      // Configuration grammaires (pour reconnaissance spécifique)
      if (grammars.length > 0 && (window as any).SpeechGrammarList) {
        const speechRecognitionList = new (window as any).SpeechGrammarList();
        grammars.forEach(grammar => {
          speechRecognitionList.addFromString(grammar.grammar, grammar.weight || 1);
        });
        recognition.grammars = speechRecognitionList;
      }

      // Event handlers
      recognition.onstart = handleStart;
      recognition.onresult = handleResult;
      recognition.onend = handleEnd;
      recognition.onerror = handleError;
      recognition.onsoundstart = handleSoundStart;
      recognition.onsoundend = handleSoundEnd;
      recognition.onspeechstart = handleSpeechStart;
      recognition.onspeechend = handleSpeechEnd;
      recognition.onaudiostart = handleAudioStart;
      recognition.onaudioend = handleAudioEnd;

      recognitionRef.current = recognition;
      setIsInitialized(true);
      console.log('🎤 Recognition initialisée:', {
        language,
        continuous,
        interimResults,
        maxAlternatives,
      });

    } catch (error) {
      console.error('🎤 Erreur initialisation recognition:', error);
      setError('Erreur initialisation reconnaissance vocale');
    }
  }, [language, continuous, interimResults, maxAlternatives, serviceURI, grammars]);

  // Gestion événements SpeechRecognition
  const handleStart = useCallback(() => {
    console.log('🎤 Reconnaissance vocale démarrée');
    setIsListening(true);
    setError(null);
    isListeningRef.current = true;

    // Auto-stop après 10 secondes si continuous = false
    if (!continuous) {
      timeoutRef.current = setTimeout(() => {
        if (isListeningRef.current) {
          stopListening();
        }
      }, 10000);
    }
  }, [continuous]);

  const handleResult = useCallback((event: SpeechRecognitionEvent) => {
    let interimText = '';
    let finalText = '';
    let maxConfidence = 0;

    // Traitement des résultats
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      const resultText = result[0].transcript;
      const resultConfidence = result[0].confidence || 0;

      if (result.isFinal) {
        finalText += resultText;
        maxConfidence = Math.max(maxConfidence, resultConfidence);
      } else {
        interimText += resultText;
      }
    }

    // Mise à jour des états
    if (interimText) {
      setInterimTranscript(interimText);
      setTranscript(interimText);
    }

    if (finalText) {
      setFinalTranscript(prev => prev + finalText);
      setTranscript(prev => prev + finalText);
      setConfidence(maxConfidence);
      
      console.log('🎤 Résultat final:', {
        text: finalText,
        confidence: maxConfidence,
      });
    }

    // Arrêt automatique si pas continuous et résultat final
    if (!continuous && finalText) {
      setTimeout(stopListening, 500);
    }
  }, [continuous]);

  const handleEnd = useCallback(() => {
    console.log('🎤 Reconnaissance vocale terminée');
    setIsListening(false);
    isListeningRef.current = false;
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    // Redémarrage automatique si continuous et pas d'erreur
    if (continuous && !error && isListeningRef.current) {
      setTimeout(() => {
        if (recognitionRef.current && isListeningRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            console.warn('🎤 Erreur redémarrage automatique:', e);
          }
        }
      }, 100);
    }
  }, [continuous, error]);

  const handleError = useCallback((event: SpeechRecognitionErrorEvent) => {
    console.error('🎤 Erreur reconnaissance vocale:', event.error, event.message);
    
    const errorMessages: Record<string, string> = {
      'no-speech': 'Aucune parole détectée. Parlez plus fort ou vérifiez votre microphone.',
      'audio-capture': 'Impossible d\'accéder au microphone. Vérifiez les permissions.',
      'not-allowed': 'Accès au microphone refusé. Autorisez l\'accès dans les paramètres du navigateur.',
      'network': 'Erreur réseau. Vérifiez votre connexion internet.',
      'service-not-allowed': 'Service de reconnaissance vocale non autorisé.',
      'bad-grammar': 'Erreur de grammaire dans la configuration.',
      'language-not-supported': `Langue ${language} non supportée.`,
      'aborted': 'Reconnaissance vocale interrompue.',
    };

    const errorMessage = errorMessages[event.error] || `Erreur inconnue: ${event.error}`;
    setError(errorMessage);
    setIsListening(false);
    isListeningRef.current = false;

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, [language]);

  // Handlers audio optionnels pour feedback utilisateur
  const handleSoundStart = useCallback(() => {
    console.log('🔊 Détection audio démarrée');
  }, []);

  const handleSoundEnd = useCallback(() => {
    console.log('🔇 Détection audio terminée');
  }, []);

  const handleSpeechStart = useCallback(() => {
    console.log('🗣️ Détection parole démarrée');
  }, []);

  const handleSpeechEnd = useCallback(() => {
    console.log('🤐 Détection parole terminée');
  }, []);

  const handleAudioStart = useCallback(() => {
    console.log('🎙️ Capture audio démarrée');
  }, []);

  const handleAudioEnd = useCallback(() => {
    console.log('🎙️ Capture audio terminée');
  }, []);

  // Fonction pour démarrer l'écoute
  const startListening = useCallback(() => {
    if (!isSupported || !recognitionRef.current || isListening) {
      return;
    }

    try {
      setError(null);
      setTranscript('');
      setInterimTranscript('');
      recognitionRef.current.start();
      console.log('🎤 Démarrage reconnaissance vocale demandé');
    } catch (error: any) {
      console.error('🎤 Erreur démarrage:', error);
      if (error.name === 'InvalidStateError') {
        // Recognition déjà en cours, on l'arrête et redémarre
        recognitionRef.current.stop();
        setTimeout(() => {
          if (recognitionRef.current) {
            recognitionRef.current.start();
          }
        }, 100);
      } else {
        setError(`Erreur démarrage: ${error.message}`);
      }
    }
  }, [isSupported, isListening]);

  // Fonction pour arrêter l'écoute
  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) {
      return;
    }

    try {
      isListeningRef.current = false;
      recognitionRef.current.stop();
      console.log('🎤 Arrêt reconnaissance vocale demandé');

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    } catch (error: any) {
      console.error('🎤 Erreur arrêt:', error);
      setError(`Erreur arrêt: ${error.message}`);
    }
  }, [isListening]);

  // Fonction pour abandonner (arrêt immédiat)
  const abortListening = useCallback(() => {
    if (!recognitionRef.current) {
      return;
    }

    try {
      isListeningRef.current = false;
      recognitionRef.current.abort();
      setIsListening(false);
      setError(null);
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }

      console.log('🎤 Reconnaissance vocale abandonnée');
    } catch (error: any) {
      console.error('🎤 Erreur abandon:', error);
    }
  }, []);

  // Fonction pour réinitialiser le transcript
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setFinalTranscript('');
    setConfidence(0);
    setError(null);
    console.log('🎤 Transcript réinitialisé');
  }, []);

  // Test du support microphone
  const testMicrophone = useCallback(async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('🎙️ Erreur test microphone:', error);
      return false;
    }
  }, []);

  // Création de grammaires pour commandes spécifiques
  const createGrammar = useCallback((commands: string[], weight: number = 1) => {
    const grammar = '#JSGF V1.0; grammar commands; public <command> = ' + 
      commands.join(' | ') + ' ;';
    return { grammar, weight };
  }, []);

  return {
    // États principaux
    isSupported,
    isListening,
    transcript,
    interimTranscript,
    finalTranscript,
    confidence,
    error,
    isInitialized,

    // Actions
    startListening,
    stopListening,
    abortListening,
    resetTranscript,
    testMicrophone,
    createGrammar,

    // Utilitaires
    browserSupport: {
      speechRecognition: isSupported,
      mediaDevices: !!navigator.mediaDevices?.getUserMedia,
      webkitSpeechRecognition: !!(window as any).webkitSpeechRecognition,
      mozSpeechRecognition: !!(window as any).mozSpeechRecognition,
    },

    // Configuration actuelle
    config: {
      language,
      continuous,
      interimResults,
      maxAlternatives,
    },
  };
};

export default useVoiceRecognition;