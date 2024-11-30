import React, { useState } from 'react';
import axios from 'axios';
import { URL } from './web-config';
import { TextField, Button, Typography } from '@mui/material';

const AddStrategyForm = () => {
  const [strategyName, setStrategyName] = useState('');
  const [strategyCode, setStrategyCode] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setStrategyCode(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!strategyName || !strategyCode) {
      setError('Пожалуйста, заполните все поля.');
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
    } catch (error) {
      setError('Ошибка при добавлении стратегии');
      console.error('Error adding strategy:', error);
    }
  };

  return (
    <div className='add-strategy-form'>
      <Typography variant='h5'>Добавить стратегию</Typography>
      <form onSubmit={handleSubmit}>
        <TextField
          label='Название стратегии'
          variant='outlined'
          value={strategyName}
          onChange={(e) => setStrategyName(e.target.value)}
          fullWidth
          required
          margin='normal'
        />
        <input
          type='file'
          accept='.zip,.js,.py'
          onChange={handleFileChange}
          required
        />
        <Button variant='contained' color='primary' type='submit'>
          Добавить
        </Button>
      </form>
      {error && <Typography color='error'>{error}</Typography>}
    </div>
  );
};

export default AddStrategyForm;
