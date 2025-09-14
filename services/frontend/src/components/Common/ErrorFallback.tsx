import React from 'react';
import { Box, Button, Typography, Container, Card, CardContent } from '@mui/material';
import { Error as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <Card sx={{ maxWidth: 600, width: '100%' }}>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom color="error">
              Oups ! Une erreur s'est produite
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Une erreur inattendue s'est produite dans l'application.
            </Typography>
            <Box sx={{ backgroundColor: '#f5f5f5', p: 2, borderRadius: 1, mb: 3 }}>
              <Typography variant="body2" component="pre" sx={{ fontSize: '0.8rem', textAlign: 'left' }}>
                {error.message}
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={resetErrorBoundary}
              size="large"
            >
              Réessayer
            </Button>
          </CardContent>
        </Card>
      </Box>
    </Container>
  );
};

export default ErrorFallback;