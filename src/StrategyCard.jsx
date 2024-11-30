import React from 'react';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import StrategyGraph from './StrategyGraph';
import axios from 'axios';
import { URL } from './web-config';

const StrategyCard = ({ strategy, stats, plotUrl, onDelete }) => {
  const fieldsToRender = ['Return [%]', 'SQN', '# Trades', 'Win Rate [%]'];

  const handleDelete = () => {
    axios
      .delete(`${URL}/delete_strategy`, {
        data: { strategy_name: strategy },
        headers: {
          'Content-Type': 'application/json',
        },
      })
      .then(() => {
        if (onDelete) {
          onDelete(strategy); // Уведомляем родительский компонент
        }
      })
      .catch((error) => console.error('Error deleting strategy:', error));
  };

  return (
    <>
      <div className='flex gap-4 flex-row-reverse'>
        <div className='bg-blue-100 w-[600px] py-4 px-2 flex flex-col gap-2 border border-black rounded'>
          <Typography variant='h4' className='text-center'>
            {strategy}
          </Typography>
          {stats ? (
            fieldsToRender.map((field) => (
              <Typography key={field}>
                {field}: {stats?.backtest_summary?.[field] || 'Н/A'}
              </Typography>
            ))
          ) : (
            <div>Загрузка...</div>
          )}
          <Button
            variant='contained'
            color='error'
            onClick={handleDelete}
            className='mt-4'
          >
            Удалить стратегию
          </Button>
        </div>
        <StrategyGraph plotUrl={plotUrl} strategyName={strategy} />
      </div>
      <hr className='border-t border-black w-full opacity-25' />
    </>
  );
};

export default StrategyCard;
