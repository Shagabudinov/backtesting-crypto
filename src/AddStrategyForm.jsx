// src/components/AddStrategyForm.jsx

import React, { useState } from 'react';
import axios from 'axios';
import { URL } from './web-config';
import { Button, Typography, Box } from '@mui/material';
import PropTypes from 'prop-types';

const AddStrategyForm = ({ setRenderCount }) => {
  const [strategyName, setStrategyName] = useState('');
  const [strategyCode, setStrategyCode] = useState(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Utility function to extract file name without extension
  const getFileNameWithoutExtension = (filename) => {
    const lastDotIndex = filename.lastIndexOf('.');
    return lastDotIndex !== -1 ? filename.substring(0, lastDotIndex) : filename;
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setStrategyCode(file);
      const extractedName = getFileNameWithoutExtension(file.name);
      setStrategyName(extractedName);
      setError('');
      setSuccessMessage('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!strategyName || !strategyCode) {
      setError('Пожалуйста, выберите файл стратегии.');
      return;
    }

    const formData = new FormData();
    formData.append('strategy_name', strategyName);
    formData.append('strategy_code', strategyCode);

    try {
      const response = await axios.post(`${URL}/add_strategy`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('Стратегия добавлена:', response.data);
      setSuccessMessage('Стратегия успешно добавлена!');
      setStrategyName('');
      setStrategyCode(null);
      // Reset the file input
      e.target.reset();
    } catch (error) {
      setError('Ошибка при добавлении стратегии');
      console.error('Error adding strategy:', error);
    } finally {
      setRenderCount(prev => prev + 1);
    }

  };

  return (
    <Box
      className='add-strategy-form'
      sx={{ maxWidth: 500, margin: '0 auto', padding: 2 }}
    >
      <Typography variant='h5' gutterBottom>
        Добавить стратегию
      </Typography>
      <form onSubmit={handleSubmit} encType='multipart/form-data'>
        {/* Display Extracted Strategy Name */}
        {strategyName && (
          <Box mb={2}>
            <Typography variant='subtitle1'>Название стратегии:</Typography>
            <Typography variant='body1' color='primary'>
              {strategyName}
            </Typography>
          </Box>
        )}

        {/* File Input */}
        <Box mb={2}>
          <Button
            variant='contained'
            component='label'
            fullWidth
            color='secondary'
          >
            Выбрать файл стратегии
            <input
              type='file'
              accept='.zip,.js,.py'
              hidden
              onChange={handleFileChange}
            />
          </Button>
          {/* Display Selected File Name */}
          {strategyCode && (
            <Typography variant='body2' mt={1}>
              Выбранный файл: {strategyCode.name}
            </Typography>
          )}
        </Box>

        {/* Submit Button */}
        <Button
          variant='contained'
          color='primary'
          type='submit'
          fullWidth
          disabled={!strategyCode}
        >
          Добавить
        </Button>
      </form>

      {/* Error Message */}
      {error && (
        <Typography color='error' mt={2}>
          {error}
        </Typography>
      )}

      {/* Success Message */}
      {successMessage && (
        <Typography color='success.main' mt={2}>
          {successMessage}
        </Typography>
      )}
    </Box>
  );
};

// Optional: Add PropTypes for better type checking
AddStrategyForm.propTypes = {
  // No props are being passed currently
};

export default AddStrategyForm;
