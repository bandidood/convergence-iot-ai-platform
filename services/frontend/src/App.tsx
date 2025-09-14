/**
 * =============================================================================
 * APP COMPONENT - Station Traffeyère IoT/AI Platform
 * Composant principal React avec routing - RNCP 39394
 * =============================================================================
 */

import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress, Container, Typography } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { ErrorBoundary } from 'react-error-boundary';

import Layout from './components/Layout/Layout';
import LoadingScreen from './components/Common/LoadingScreen';
import ErrorFallback from './components/Common/ErrorFallback';

// Lazy loading des composants pour optimiser les performances
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));
const Sensors = lazy(() => import('./pages/Sensors/Sensors'));
const Analytics = lazy(() => import('./pages/Analytics/Analytics'));
const XAIDashboard = lazy(() => import('./pages/XAI/XAIDashboard'));
const DigitalTwin = lazy(() => import('./pages/DigitalTwin/DigitalTwin'));
const Settings = lazy(() => import('./pages/Settings/Settings'));
const NotFound = lazy(() => import('./pages/NotFound/NotFound'));

// Composant de fallback pour le Suspense
const PageLoader: React.FC = () => (
  <Container maxWidth="lg" sx={{ py: 4 }}>
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="60vh"
      gap={2}
    >
      <CircularProgress size={48} thickness={4} />
      <Typography variant="body1" color="text.secondary">
        Chargement en cours...
      </Typography>
    </Box>
  </Container>
);

// Configuration des métadonnées SEO
const AppMetadata: React.FC = () => (
  <Helmet>
    <title>Station Traffeyère IoT/AI Platform - RNCP 39394</title>
    <meta
      name="description"
      content="Plateforme IoT/IA convergente pour la transformation digitale des infrastructures critiques de traitement des eaux. Expert en Systèmes d'Information et Sécurité - RNCP 39394."
    />
    <meta
      name="keywords"
      content="IoT, Intelligence Artificielle, Station épuration, Monitoring temps réel, Digital Twin, Edge AI, Cybersécurité, RNCP 39394"
    />
    <meta name="author" content="Johann Lebel" />
    <meta property="og:title" content="Station Traffeyère IoT/AI Platform" />
    <meta
      property="og:description"
      content="Plateforme IoT/IA convergente pour infrastructures critiques - RNCP 39394"
    />
    <meta property="og:type" content="website" />
    <meta property="og:locale" content="fr_FR" />
    
    {/* Schema.org structured data */}
    <script type="application/ld+json">
      {JSON.stringify({
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Station Traffeyère IoT/AI Platform",
        "description": "Plateforme IoT/IA convergente pour transformation digitale des infrastructures critiques",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "author": {
          "@type": "Person",
          "name": "Johann Lebel",
          "description": "Expert en Systèmes d'Information et Sécurité - RNCP 39394"
        },
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "EUR",
          "category": "Research & Development"
        }
      })}
    </script>
  </Helmet>
);

// Composant principal App
const App: React.FC = () => {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        console.error('🚨 Application Error Boundary:', error);
        console.error('Error Info:', errorInfo);
        
        // En production, envoyer à service de monitoring
        if (import.meta.env.NODE_ENV === 'production') {
          // Ici on pourrait envoyer à Sentry, LogRocket, etc.
          console.log('📊 Erreur rapportée au système de monitoring');
        }
      }}
      onReset={() => {
        // Cleanup ou reset de l'état si nécessaire
        window.location.reload();
      }}
    >
      <AppMetadata />
      
      <Layout>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Route principale - Redirection vers dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* Dashboard principal */}
            <Route path="/dashboard" element={<Dashboard />} />
            
            {/* Gestion des capteurs IoT */}
            <Route path="/sensors" element={<Sensors />} />
            
            {/* Analyses et métriques */}
            <Route path="/analytics" element={<Analytics />} />
            
            {/* IA Explicable */}
            <Route path="/xai" element={<XAIDashboard />} />
            
            {/* Digital Twin 3D */}
            <Route path="/digital-twin" element={<DigitalTwin />} />
            
            {/* Paramètres et configuration */}
            <Route path="/settings" element={<Settings />} />
            
            {/* Page 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </Layout>
    </ErrorBoundary>
  );
};

export default App;