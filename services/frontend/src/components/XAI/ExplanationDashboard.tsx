import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  Tab,
  Tabs,
  Alert,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Psychology,
  AutoGraph,
  ChatBubble,
  Visibility,
  Settings,
  TrendingUp,
  QuestionAnswer,
  Science,
  Analytics,
  ModelTraining,
  BrightnessMedium,
  Close,
  Download,
  Share,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { Line, Bar, Radar } from 'react-chartjs-2';

import { useXAIExplanations } from '@hooks/useXAIExplanations';
import { useIoTData } from '@hooks/useIoTData';
import SHAPVisualizer from './SHAPVisualizer';
import ConversationalAI from './ConversationalAI';
import UncertaintyQuantification from './UncertaintyQuantification';
import ExplanationHistory from './ExplanationHistory';
import { XAIExplanation, ExplanationLevel, FeatureImportance } from '@types/xai.types';

interface ExplanationDashboardProps {
  selectedSensorId?: string;
  expertiseLevel?: 'novice' | 'intermediate' | 'expert' | 'researcher';
  onClose?: () => void;
}

const ExplanationDashboard: React.FC<ExplanationDashboardProps> = ({
  selectedSensorId,
  expertiseLevel = 'intermediate',
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [explanationLevel, setExplanationLevel] = useState<ExplanationLevel>(expertiseLevel);
  const [realTimeMode, setRealTimeMode] = useState(true);
  const [showChatbot, setShowChatbot] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState<'shap' | 'lime' | 'hybrid'>('hybrid');
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [selectedTimestamp, setSelectedTimestamp] = useState<Date | null>(null);

  // Hooks personnalisés
  const { 
    explanation, 
    loading, 
    error, 
    generateExplanation,
    methods 
  } = useXAIExplanations(selectedSensorId);
  const { sensors } = useIoTData();

  // Référence pour auto-scroll des explications
  const explanationRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedSensorId && realTimeMode) {
      // Génération d'explications en temps réel
      const interval = setInterval(() => {
        generateExplanation({
          sensorId: selectedSensorId,
          method: selectedMethod,
          expertiseLevel: explanationLevel,
          includeUncertainty: true,
        });
      }, 10000); // Toutes les 10 secondes

      return () => clearInterval(interval);
    }
  }, [selectedSensorId, selectedMethod, explanationLevel, realTimeMode, generateExplanation]);

  // Génération d'explication initiale
  useEffect(() => {
    if (selectedSensorId) {
      generateExplanation({
        sensorId: selectedSensorId,
        method: selectedMethod,
        expertiseLevel: explanationLevel,
        includeUncertainty: true,
      });
    }
  }, [selectedSensorId, selectedMethod, explanationLevel, generateExplanation]);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleExportExplanation = () => {
    if (explanation) {
      // Export au format JSON pour analyse ultérieure
      const exportData = {
        timestamp: new Date().toISOString(),
        sensorId: selectedSensorId,
        explanation: explanation,
        method: selectedMethod,
        expertiseLevel: explanationLevel,
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `xai-explanation-${selectedSensorId}-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const currentSensor = sensors?.find(s => s.id === selectedSensorId);

  if (loading && !explanation) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>
          Génération d'explications IA...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Erreur lors de la génération d'explications: {error.message}
      </Alert>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header de contrôle XAI */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Paper sx={{ p: 2, mb: 2, borderRadius: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Psychology sx={{ fontSize: 32, color: 'primary.main' }} />
              <Box>
                <Typography variant="h5" fontWeight="bold">
                  IA Explicable - Station Traffeyère
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
                  {currentSensor && (
                    <Chip
                      label={`Capteur ${currentSensor.name}`}
                      color="primary"
                      icon={<Analytics />}
                    />
                  )}
                  <Chip
                    label={`Méthode: ${selectedMethod.toUpperCase()}`}
                    color="secondary"
                    icon={<ModelTraining />}
                  />
                  <Chip
                    label={`Niveau: ${explanationLevel}`}
                    color="info"
                    icon={<BrightnessMedium />}
                  />
                  {explanation && (
                    <Chip
                      label={`Confiance: ${Math.round(explanation.confidence * 100)}%`}
                      color={explanation.confidence > 0.8 ? 'success' : 'warning'}
                      icon={<TrendingUp />}
                    />
                  )}
                </Box>
              </Box>
            </Box>

            {/* Contrôles */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Méthode</InputLabel>
                <Select
                  value={selectedMethod}
                  label="Méthode"
                  onChange={(e) => setSelectedMethod(e.target.value as any)}
                >
                  <MenuItem value="shap">SHAP</MenuItem>
                  <MenuItem value="lime">LIME</MenuItem>
                  <MenuItem value="hybrid">Hybride</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 140 }}>
                <InputLabel>Niveau Expert</InputLabel>
                <Select
                  value={explanationLevel}
                  label="Niveau Expert"
                  onChange={(e) => setExplanationLevel(e.target.value as ExplanationLevel)}
                >
                  <MenuItem value="novice">Novice</MenuItem>
                  <MenuItem value="intermediate">Intermédiaire</MenuItem>
                  <MenuItem value="expert">Expert</MenuItem>
                  <MenuItem value="researcher">Chercheur</MenuItem>
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={realTimeMode}
                    onChange={(e) => setRealTimeMode(e.target.checked)}
                  />
                }
                label="Temps réel"
              />

              <Tooltip title="Chatbot XAI">
                <IconButton
                  color="primary"
                  onClick={() => setShowChatbot(true)}
                >
                  <ChatBubble />
                </IconButton>
              </Tooltip>

              <Tooltip title="Exporter">
                <IconButton onClick={handleExportExplanation}>
                  <Download />
                </IconButton>
              </Tooltip>

              {onClose && (
                <Tooltip title="Fermer">
                  <IconButton onClick={onClose}>
                    <Close />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Box>
        </Paper>
      </motion.div>

      {/* Onglets principaux */}
      <Paper sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<AutoGraph />} label="Visualisations SHAP" />
          <Tab icon={<Science />} label="Incertitude & Confiance" />
          <Tab icon={<Analytics />} label="Analyse Comparative" />
          <Tab icon={<QuestionAnswer />} label="Historique" />
        </Tabs>

        <Box sx={{ flexGrow: 1, p: 2 }}>
          <AnimatePresence mode="wait">
            {/* Onglet 1: Visualisations SHAP */}
            {activeTab === 0 && (
              <motion.div
                key="shap"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <Grid container spacing={3} sx={{ height: '100%' }}>
                  {/* Visualisation principale SHAP */}
                  <Grid item xs={12} lg={8}>
                    <Paper sx={{ p: 2, height: '400px' }}>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Contribution des Caractéristiques (SHAP)
                      </Typography>
                      <SHAPVisualizer
                        explanation={explanation}
                        method={selectedMethod}
                        interactive={true}
                        height={340}
                      />
                    </Paper>
                  </Grid>

                  {/* Panneau de contrôle */}
                  <Grid item xs={12} lg={4}>
                    <Paper sx={{ p: 2, height: '400px' }}>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Paramètres d'Explication
                      </Typography>

                      <Box sx={{ mb: 3 }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          Seuil de confiance: {Math.round(confidenceThreshold * 100)}%
                        </Typography>
                        <Slider
                          value={confidenceThreshold}
                          onChange={(_, value) => setConfidenceThreshold(value as number)}
                          min={0.1}
                          max={1.0}
                          step={0.05}
                          marks={[
                            { value: 0.5, label: '50%' },
                            { value: 0.8, label: '80%' },
                            { value: 0.95, label: '95%' },
                          ]}
                        />
                      </Box>

                      {explanation && (
                        <Box>
                          <Divider sx={{ my: 2 }} />
                          <Typography variant="subtitle2" sx={{ mb: 2 }}>
                            Métriques Actuelles
                          </Typography>

                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                              Confiance Prédiction
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={explanation.confidence * 100}
                              color={explanation.confidence > 0.8 ? 'success' : 'warning'}
                              sx={{ height: 8, borderRadius: 1, mt: 0.5 }}
                            />
                            <Typography variant="caption">
                              {Math.round(explanation.confidence * 100)}%
                            </Typography>
                          </Box>

                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                              Qualité Explication
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={explanation.explanationQuality * 100}
                              color="info"
                              sx={{ height: 8, borderRadius: 1, mt: 0.5 }}
                            />
                            <Typography variant="caption">
                              {Math.round(explanation.explanationQuality * 100)}%
                            </Typography>
                          </Box>

                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                              Temps de Génération
                            </Typography>
                            <Typography variant="h6">
                              {explanation.processingTime}ms
                            </Typography>
                            <Typography variant="caption" color="success.main">
                              Objectif: &lt; 100ms
                            </Typography>
                          </Box>
                        </Box>
                      )}
                    </Paper>
                  </Grid>

                  {/* Explication textuelle adaptative */}
                  <Grid item xs={12}>
                    <Paper sx={{ p: 2, maxHeight: '200px', overflow: 'auto' }} ref={explanationRef}>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Explication Contextuelle
                      </Typography>
                      {explanation?.naturalLanguageExplanation ? (
                        <Typography variant="body1" sx={{ lineHeight: 1.8 }}>
                          {explanation.naturalLanguageExplanation}
                        </Typography>
                      ) : (
                        <Alert severity="info">
                          Aucune explication disponible. Sélectionnez un capteur pour voir les explications IA.
                        </Alert>
                      )}
                    </Paper>
                  </Grid>
                </Grid>
              </motion.div>
            )}

            {/* Onglet 2: Incertitude & Confiance */}
            {activeTab === 1 && (
              <motion.div
                key="uncertainty"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <UncertaintyQuantification
                  explanation={explanation}
                  sensorId={selectedSensorId}
                  method={selectedMethod}
                />
              </motion.div>
            )}

            {/* Onglet 3: Analyse Comparative */}
            {activeTab === 2 && (
              <motion.div
                key="comparative"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2, height: '400px' }}>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Comparaison Méthodes XAI
                      </Typography>
                      {/* Graphique comparatif SHAP vs LIME */}
                      <Box sx={{ height: 340 }}>
                        {explanation && (
                          <Bar
                            data={{
                              labels: Object.keys(explanation.featureImportances).slice(0, 10),
                              datasets: [
                                {
                                  label: 'SHAP',
                                  data: Object.values(explanation.featureImportances).slice(0, 10),
                                  backgroundColor: 'rgba(54, 162, 235, 0.8)',
                                },
                                {
                                  label: 'LIME (estimé)',
                                  data: Object.values(explanation.featureImportances).slice(0, 10).map(v => v * 0.9),
                                  backgroundColor: 'rgba(255, 99, 132, 0.8)',
                                },
                              ],
                            }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: {
                                legend: { position: 'top' },
                                title: {
                                  display: true,
                                  text: 'Importance des caractéristiques'
                                }
                              },
                              scales: {
                                y: {
                                  beginAtZero: true,
                                  title: { display: true, text: 'Impact sur prédiction' }
                                }
                              }
                            }}
                          />
                        )}
                      </Box>
                    </Paper>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2, height: '400px' }}>
                      <Typography variant="h6" sx={{ mb: 2 }}>
                        Performance Temps Réel
                      </Typography>
                      <Box sx={{ height: 340 }}>
                        {/* Graphique de performance */}
                        <Line
                          data={{
                            labels: ['09:00', '09:05', '09:10', '09:15', '09:20', '09:25', '09:30'],
                            datasets: [
                              {
                                label: 'Temps génération (ms)',
                                data: [67, 72, 69, 65, 71, 68, 64],
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                tension: 0.1,
                              },
                              {
                                label: 'Confiance (%)',
                                data: [94, 92, 95, 97, 93, 96, 94],
                                borderColor: 'rgb(255, 99, 132)',
                                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                yAxisID: 'y1',
                                tension: 0.1,
                              },
                            ],
                          }}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                              mode: 'index' as const,
                              intersect: false,
                            },
                            scales: {
                              x: { display: true, title: { display: true, text: 'Temps' } },
                              y: {
                                type: 'linear' as const,
                                display: true,
                                position: 'left' as const,
                                title: { display: true, text: 'Temps (ms)' },
                              },
                              y1: {
                                type: 'linear' as const,
                                display: true,
                                position: 'right' as const,
                                title: { display: true, text: 'Confiance (%)' },
                                grid: { drawOnChartArea: false },
                              },
                            },
                          }}
                        />
                      </Box>
                    </Paper>
                  </Grid>
                </Grid>
              </motion.div>
            )}

            {/* Onglet 4: Historique */}
            {activeTab === 3 && (
              <motion.div
                key="history"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <ExplanationHistory
                  sensorId={selectedSensorId}
                  onSelectExplanation={(timestamp) => setSelectedTimestamp(timestamp)}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </Box>
      </Paper>

      {/* Dialog Chatbot Conversationnel */}
      <Dialog
        open={showChatbot}
        onClose={() => setShowChatbot(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { height: '80vh' }
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <ChatBubble color="primary" />
            <Typography variant="h6">
              Assistant IA Explicable
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0, height: '100%' }}>
          <ConversationalAI
            currentExplanation={explanation}
            sensorId={selectedSensorId}
            expertiseLevel={explanationLevel}
            onClose={() => setShowChatbot(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default ExplanationDashboard;