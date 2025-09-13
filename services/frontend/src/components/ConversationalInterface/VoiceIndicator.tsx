import React from 'react';
import { Box, Tooltip, IconButton } from '@mui/material';
import {
  Mic as MicIcon,
  MicOff as MicOffIcon,
  VolumeUp as VolumeUpIcon,
  Error as ErrorIcon,
  Hearing as HearingIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceIndicatorProps {
  listening?: boolean;
  speaking?: boolean;
  error?: string | null;
  size?: 'small' | 'medium' | 'large';
  interactive?: boolean;
  onToggleListening?: () => void;
  onToggleSpeaking?: () => void;
  style?: React.CSSProperties;
}

const VoiceIndicator: React.FC<VoiceIndicatorProps> = ({
  listening = false,
  speaking = false,
  error = null,
  size = 'medium',
  interactive = false,
  onToggleListening,
  onToggleSpeaking,
  style = {},
}) => {
  // Configuration des tailles
  const sizeConfig = {
    small: {
      container: 32,
      icon: 16,
      ripple: 40,
      fontSize: 12,
    },
    medium: {
      container: 48,
      icon: 24,
      ripple: 60,
      fontSize: 14,
    },
    large: {
      container: 64,
      icon: 32,
      ripple: 80,
      fontSize: 16,
    },
  };

  const config = sizeConfig[size];

  // Animations pour les états
  const pulseAnimation = {
    scale: [1, 1.2, 1],
    opacity: [0.7, 1, 0.7],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  };

  const rotateAnimation = {
    rotate: [0, 360],
    scale: [1, 1.1, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'linear',
    },
  };

  const rippleAnimation = {
    scale: [0, 2],
    opacity: [0.8, 0],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeOut',
    },
  };

  // Couleurs selon l'état
  const getColors = () => {
    if (error) {
      return {
        primary: '#f44336',
        secondary: '#ffebee',
        ripple: '#f44336',
      };
    }
    if (speaking) {
      return {
        primary: '#4caf50',
        secondary: '#e8f5e8',
        ripple: '#4caf50',
      };
    }
    if (listening) {
      return {
        primary: '#2196f3',
        secondary: '#e3f2fd',
        ripple: '#2196f3',
      };
    }
    return {
      primary: '#9e9e9e',
      secondary: '#f5f5f5',
      ripple: '#9e9e9e',
    };
  };

  const colors = getColors();

  // Icône selon l'état
  const getIcon = () => {
    if (error) return <ErrorIcon sx={{ fontSize: config.icon }} />;
    if (speaking) return <VolumeUpIcon sx={{ fontSize: config.icon }} />;
    if (listening) return <MicIcon sx={{ fontSize: config.icon }} />;
    return <MicOffIcon sx={{ fontSize: config.icon }} />;
  };

  // Message tooltip
  const getTooltipMessage = () => {
    if (error) return `Erreur: ${error}`;
    if (speaking) return 'Synthèse vocale active';
    if (listening) return 'Écoute en cours...';
    return 'Micro désactivé';
  };

  // Composant principal
  const IndicatorContent = () => (
    <Box
      sx={{
        position: 'relative',
        width: config.container,
        height: config.container,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Onde de propagation (ripple) */}
      <AnimatePresence>
        {(listening || speaking) && (
          <>
            {[...Array(3)].map((_, index) => (
              <motion.div
                key={`ripple-${index}`}
                style={{
                  position: 'absolute',
                  width: config.ripple,
                  height: config.ripple,
                  borderRadius: '50%',
                  border: `2px solid ${colors.ripple}`,
                  opacity: 0.3,
                }}
                animate={rippleAnimation}
                transition={{
                  ...rippleAnimation.transition,
                  delay: index * 0.5,
                }}
              />
            ))}
          </>
        )}
      </AnimatePresence>

      {/* Indicateur principal */}
      <motion.div
        animate={
          listening ? pulseAnimation : 
          speaking ? rotateAnimation : 
          { scale: 1, opacity: 1 }
        }
        style={{
          width: config.container,
          height: config.container,
          borderRadius: '50%',
          backgroundColor: colors.secondary,
          border: `2px solid ${colors.primary}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.primary,
          cursor: interactive ? 'pointer' : 'default',
          zIndex: 1,
        }}
        onClick={interactive ? (listening ? onToggleListening : onToggleSpeaking) : undefined}
        whileHover={interactive ? { scale: 1.05 } : {}}
        whileTap={interactive ? { scale: 0.95 } : {}}
      >
        {getIcon()}
      </motion.div>

      {/* Indicateur d'activité pour l'écoute */}
      <AnimatePresence>
        {listening && (
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0 }}
            style={{
              position: 'absolute',
              top: -4,
              right: -4,
              width: 12,
              height: 12,
              borderRadius: '50%',
              backgroundColor: '#4caf50',
              zIndex: 2,
            }}
          />
        )}
      </AnimatePresence>

      {/* Barres d'amplitude pour la synthèse */}
      <AnimatePresence>
        {speaking && (
          <Box
            component={motion.div}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            sx={{
              position: 'absolute',
              bottom: -16,
              display: 'flex',
              gap: 0.5,
              alignItems: 'end',
            }}
          >
            {[...Array(5)].map((_, index) => (
              <motion.div
                key={`bar-${index}`}
                style={{
                  width: 3,
                  backgroundColor: colors.primary,
                  borderRadius: '2px',
                }}
                animate={{
                  height: [4, 12, 4],
                }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  delay: index * 0.1,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </Box>
        )}
      </AnimatePresence>

      {/* Indicateur d'erreur */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            style={{
              position: 'absolute',
              bottom: -24,
              fontSize: config.fontSize,
              color: colors.primary,
              fontWeight: 'bold',
              textAlign: 'center',
              whiteSpace: 'nowrap',
              maxWidth: 120,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            Erreur audio
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );

  // Rendu avec ou sans tooltip
  if (interactive) {
    return (
      <Tooltip title={getTooltipMessage()} placement="top">
        <IconButton
          size={size}
          style={style}
          sx={{
            padding: 0,
            '&:hover': {
              backgroundColor: 'transparent',
            },
          }}
        >
          <IndicatorContent />
        </IconButton>
      </Tooltip>
    );
  }

  return (
    <Tooltip title={getTooltipMessage()} placement="top">
      <Box style={style}>
        <IndicatorContent />
      </Box>
    </Tooltip>
  );
};

// Composant spécialisé pour l'état d'écoute
export const ListeningIndicator: React.FC<{
  active: boolean;
  size?: 'small' | 'medium' | 'large';
  style?: React.CSSProperties;
}> = ({ active, size = 'medium', style }) => (
  <VoiceIndicator
    listening={active}
    size={size}
    style={style}
  />
);

// Composant spécialisé pour l'état de parole
export const SpeakingIndicator: React.FC<{
  active: boolean;
  size?: 'small' | 'medium' | 'large';
  style?: React.CSSProperties;
}> = ({ active, size = 'medium', style }) => (
  <VoiceIndicator
    speaking={active}
    size={size}
    style={style}
  />
);

// Composant compact pour la barre d'état
export const VoiceStatusBar: React.FC<{
  listening: boolean;
  speaking: boolean;
  error?: string | null;
  interactive?: boolean;
  onToggleListening?: () => void;
  onToggleSpeaking?: () => void;
}> = ({
  listening,
  speaking,
  error,
  interactive = false,
  onToggleListening,
  onToggleSpeaking,
}) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    {/* Indicateur d'écoute */}
    <VoiceIndicator
      listening={listening}
      size="small"
      interactive={interactive}
      onToggleListening={onToggleListening}
    />
    
    {/* Séparateur */}
    <Box
      sx={{
        width: 1,
        height: 20,
        backgroundColor: 'divider',
        mx: 1,
      }}
    />
    
    {/* Indicateur de parole */}
    <VoiceIndicator
      speaking={speaking}
      size="small"
      interactive={interactive}
      onToggleSpeaking={onToggleSpeaking}
      error={error}
    />
    
    {/* État textuel */}
    <Box sx={{ ml: 1 }}>
      <motion.div
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ 
          duration: 2, 
          repeat: listening || speaking ? Infinity : 0,
          ease: 'easeInOut' 
        }}
      >
        {error ? (
          <span style={{ color: '#f44336', fontSize: 12 }}>
            Erreur audio
          </span>
        ) : speaking ? (
          <span style={{ color: '#4caf50', fontSize: 12 }}>
            🔊 Synthèse active
          </span>
        ) : listening ? (
          <span style={{ color: '#2196f3', fontSize: 12 }}>
            🎤 Écoute...
          </span>
        ) : (
          <span style={{ color: '#9e9e9e', fontSize: 12 }}>
            Vocal inactif
          </span>
        )}
      </motion.div>
    </Box>
  </Box>
);

export default VoiceIndicator;