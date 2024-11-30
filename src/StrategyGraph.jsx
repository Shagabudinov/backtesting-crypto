import React, { useState } from 'react';
import Typography from '@mui/material/Typography';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { URL } from './web-config';

const StrategyGraph = ({ plotUrl, strategyName }) => {
  const [graphType, setGraphType] = useState('distribution');

  const distributionPlotUrl = `${URL}/year-graph/result_for_strategy?strategy=${strategyName}`;

  const handleChangeGraphType = (event, newGraphType) => {
    if (newGraphType !== null) {
      setGraphType(newGraphType);
    }
  };

  return (
    <div className='flex gap-[16px] relative border border-black rounded'>
      {/* Preload both iframes and toggle their visibility */}
      {plotUrl ? (
        <>
          <iframe
            src={plotUrl}
            style={{ display: graphType === 'price' ? 'block' : 'none' }}
            className='w-[834px] h-[1004px] bg-red-100 pt-[64px]'
            title={`${strategyName} Price Plot`}
          />
          <iframe
            src={distributionPlotUrl}
            style={{ display: graphType === 'distribution' ? 'block' : 'none' }}
            className='w-[834px] h-[1004px] bg-red-100 pt-[64px]'
            title={`${strategyName} Distribution Plot`}
          />
        </>
      ) : (
        <div className='w-[834px] h-[1004px] bg-red-100 pt-[64px] flex items-center justify-center'>
          Загрузка...
        </div>
      )}

      <ToggleButtonGroup
        value={graphType}
        exclusive
        onChange={handleChangeGraphType}
        aria-label='graph type'
        className='absolute top-[12px] left-[31%]'
      >
        <ToggleButton value='price'>
          <Typography>График цены</Typography>
        </ToggleButton>
        <ToggleButton value='distribution'>
          <Typography>График распределения</Typography>
        </ToggleButton>
      </ToggleButtonGroup>
    </div>
  );
};

export default StrategyGraph;
