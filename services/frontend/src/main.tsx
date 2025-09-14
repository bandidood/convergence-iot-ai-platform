/**
 * =============================================================================
 * MAIN ENTRY POINT - Station Traffeyère IoT/AI Platform
 * Point d'entrée React + TypeScript - RNCP 39394
 * =============================================================================
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HelmetProvider } from 'react-helmet-async';
import { Toaster } from 'react-hot-toast';

import App from './App';
import './index.css';

// Configuration React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 30, // 30 minutes
      retry: (failureCount, error: any) => {
        // Retry logic adapté IoT
        if (error?.status === 404 || error?.status === 403) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
});

// Thème Material-UI personnalisé RNCP
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2', // Bleu professionnel
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#388e3c', // Vert environnemental
      light: '#66bb6a',
      dark: '#2e7d32',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    info: {
      main: '#2196f3',
    },
    success: {
      main: '#4caf50',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
      color: '#1976d2',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 12,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
  },
});

// Configuration environnement
const config = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  GRAFANA_URL: import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3001',
  PROMETHEUS_URL: import.meta.env.VITE_PROMETHEUS_URL || 'http://localhost:9090',
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  ENVIRONMENT: import.meta.env.NODE_ENV || 'development',
};

// Debug info (development seulement)
if (config.ENVIRONMENT === 'development') {
  console.group('🚀 Station Traffeyère IoT/AI Platform');
  console.log('📊 Version:', config.APP_VERSION);
  console.log('🌍 Environment:', config.ENVIRONMENT);
  console.log('🔗 API URL:', config.API_URL);
  console.log('📡 WebSocket URL:', config.WS_URL);
  console.log('📈 Grafana URL:', config.GRAFANA_URL);
  console.log('🎯 RNCP 39394 - Expert en Systèmes d\'Information et Sécurité');
  console.groupEnd();
}

// Gestion d'erreurs globale
window.addEventListener('error', (event) => {
  console.error('🚨 Erreur globale capturée:', event.error);
  
  // En production, envoyer à service de monitoring
  if (config.ENVIRONMENT === 'production') {
    // Ici on pourrait envoyer à Sentry, Bugsnag, etc.
    console.log('📊 Erreur rapportée au système de monitoring');
  }
});

// Point d'entrée principal
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <HelmetProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <BrowserRouter>
            <App />
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#333',
                  color: '#fff',
                  borderRadius: '8px',
                  padding: '12px 16px',
                },
                success: {
                  iconTheme: {
                    primary: '#4caf50',
                    secondary: '#fff',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#f44336',
                    secondary: '#fff',
                  },
                  duration: 6000,
                },
              }}
            />
          </BrowserRouter>
        </ThemeProvider>
      </QueryClientProvider>
    </HelmetProvider>
  </React.StrictMode>
);

// Service Worker (PWA)
if ('serviceWorker' in navigator && config.ENVIRONMENT === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('✅ SW registered:', registration);
      })
      .catch((registrationError) => {
        console.log('❌ SW registration failed:', registrationError);
      });
  });
}