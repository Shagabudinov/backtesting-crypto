import React, { useState, useEffect } from 'react';
import Typography from '@mui/material/Typography';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { URL } from '../../web-config';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';

const StrategyGraph = ({ plotUrl, strategyName }) => {
  const [graphType, setGraphType] = useState('price');
  const [priceLoaded, setPriceLoaded] = useState(false);
  const [distributionLoaded, setDistributionLoaded] = useState(false);

  const distributionPlotUrl = `${URL}/year-graph/result_for_strategy?strategy=${strategyName}`;

  const handleChangeGraphType = (event, newGraphType) => {
    if (newGraphType !== null) {
      setGraphType(newGraphType);
    }
  };

  useEffect(() => {
    if (plotUrl) {
      const img = new Image();
      img.src = plotUrl;
      img.onload = () => setPriceLoaded(true);
    }
  }, [plotUrl]);

  useEffect(() => {
    if (distributionPlotUrl) {
      const img = new Image();
      img.src = distributionPlotUrl;
      img.onload = () => setDistributionLoaded(true);
    }
  }, [distributionPlotUrl]);

  return (
    <div className='flex gap-[16px] relative border border-black rounded'>
      {/* Price Plot */}
      {plotUrl ? (
        <iframe
          src={plotUrl}
          style={{ display: graphType === 'price' ? 'block' : 'none' }}
          className='w-[834px] h-[1004px] bg-red-100 pt-[64px]'
          title={`${strategyName} Price Plot`}
        />
      ) : plotUrl ? (
        <Box className='w-[834px] h-[1004px] bg-red-100 pt-[64px] flex items-center justify-center'>
          <CircularProgress />
        </Box>
      ) : (
        <div className='w-[834px] h-[1004px] bg-red-100 pt-[64px] flex items-center justify-center'>
          Загрузка...
        </div>
      )}

      {/* Distribution Plot */}
      {distributionPlotUrl && distributionLoaded ? (
        <iframe
          src={distributionPlotUrl}
          style={{ display: graphType === 'distribution' ? 'block' : 'none' }}
          className='w-[834px] h-[1004px] bg-red-100 pt-[64px]'
          title={`${strategyName} Distribution Plot`}
        />
      ) : distributionPlotUrl ? (
        <Box className='w-[834px] h-[1004px] bg-red-100 pt-[64px] flex items-center justify-center'>
          <CircularProgress />
        </Box>
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
