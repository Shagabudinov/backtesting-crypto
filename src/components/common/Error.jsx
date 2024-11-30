import React from 'react';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

const Error = ({ message }) => (
  <Box display='flex' justifyContent='center' alignItems='center' height='100%'>
    <Typography color='error' variant='h6'>
      {message || 'An error occurred while fetching data.'}
    </Typography>
  </Box>
);

export default Error;
