import React from 'react';
import { Typography, Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Home as HomeIcon } from '@mui/icons-material';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box textAlign="center" py={8}>
      <Typography variant="h1" color="primary" gutterBottom>
        404
      </Typography>
      <Typography variant="h4" gutterBottom>
        Page non trouvée
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        La page que vous recherchez n'existe pas.
      </Typography>
      <Button
        variant="contained"
        startIcon={<HomeIcon />}
        onClick={() => navigate('/')}
      >
        Retour au Dashboard
      </Button>
    </Box>
  );
};

export default NotFound;