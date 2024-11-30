import React from 'react';
import Typography from '@mui/material/Typography';
import StrategyGraph from '../StrategyGraph/StrategyGraph';
import PropTypes from 'prop-types';

const StrategyCard = ({ strategy, stats, plotUrl }) => {
  const fieldsToRender = ['Return [%]', 'SQN', '# Trades', 'Win Rate [%]'];

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
        </div>
        <StrategyGraph plotUrl={plotUrl} strategyName={strategy} />
      </div>
      <hr className='border-t border-black w-full opacity-25' />
    </>
  );
};

StrategyCard.propTypes = {
  strategy: PropTypes.string.isRequired,
  stats: PropTypes.object,
  plotUrl: PropTypes.string,
};

export default StrategyCard;
