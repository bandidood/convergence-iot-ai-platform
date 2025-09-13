import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // Configuration du serveur de développement
  server: {
    port: 3000,
    host: true, // Écoute sur toutes les interfaces pour Docker
    proxy: {
      // Proxy vers l'API backend
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false
      },
      // Proxy vers WebSocket
      '/socket.io': {
        target: 'http://backend:8000',
        ws: true,
        changeOrigin: true
      },
      // Proxy vers Digital Twin Unity
      '/unity': {
        target: 'http://digital-twin:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/unity/, '')
      }
    }
  },

  // Configuration build optimisée
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false, // Désactivé pour production
    minify: 'terser',
    target: 'esnext',
    
    // Configuration rollup pour optimisation
    rollupOptions: {
      output: {
        manualChunks: {
          // Séparation des vendors pour meilleur caching
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material'],
          charts: ['chart.js', 'react-chartjs-2', 'd3'],
          three: ['three', '@react-three/fiber', '@react-three/drei'],
          utils: ['dayjs', 'axios', 'socket.io-client']
        }
      }
    },

    // Compression et optimisations
    terserOptions: {
      compress: {
        drop_console: true, // Retire les console.log en production
        drop_debugger: true
      }
    }
  },

  // Résolution des imports
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/components'),
      '@services': resolve(__dirname, './src/services'),
      '@hooks': resolve(__dirname, './src/hooks'),
      '@store': resolve(__dirname, './src/store'),
      '@types': resolve(__dirname, './src/types'),
      '@utils': resolve(__dirname, './src/utils'),
      '@assets': resolve(__dirname, './src/assets')
    }
  },

  // Variables d'environnement
  define: {
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    __VERSION__: JSON.stringify(process.env.npm_package_version),
  },

  // Configuration CSS
  css: {
    devSourcemap: true,
    modules: {
      localsConvention: 'camelCase'
    }
  },

  // Configuration pour les tests
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    css: true
  },

  // Optimisation des dépendances
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      '@mui/material',
      '@emotion/react',
      '@emotion/styled',
      'chart.js',
      'd3'
    ]
  }
});