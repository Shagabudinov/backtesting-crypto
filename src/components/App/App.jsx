import React, { useState, useMemo } from 'react';
import './App.css';
import Typography from '@mui/material/Typography';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import StrategyCard from '../StrategyCard/StrategyCard';
import SortSelect from '../SortSelect/SortSelect';
import Loading from '../common/Loading';
import Error from '../common/Error';
import useFetchStrategies from '../../hooks/useFetchStrategies';

const theme = createTheme({
  typography: {
    fontFamily: '"JetBrains Mono", "Arial", sans-serif',
  },
});

const App = () => {
  const { availableStrategies, strategiesStats, plots, loading, error } =
    useFetchStrategies();

  const [sortOption, setSortOption] = useState('newness_desc');

  // Handler for sort option change
  const handleSortChange = (event) => {
    setSortOption(event.target.value);
  };

  // Memoized sorted strategies
  const sortedStrategies = useMemo(() => {
    if (!availableStrategies) return [];

    const strategiesCopy = [...availableStrategies];
    const indexedStrategies = strategiesCopy.map((strategy, index) => ({
      strategy,
      index,
    }));

    indexedStrategies.sort((a, b) => {
      switch (sortOption) {
        case 'newness_asc':
          return a.index - b.index;
        case 'newness_desc':
          return b.index - a.index;
        case 'SQN_asc':
          return (
            (strategiesStats[a.strategy]?.SQN || 0) -
            (strategiesStats[b.strategy]?.SQN || 0)
          );
        case 'SQN_desc':
          return (
            (strategiesStats[b.strategy]?.backtest_summary?.SQN || 0) -
            (strategiesStats[a.strategy]?.backtest_summary?.SQN || 0)
          );
        case 'Trades_asc':
          return (
            (strategiesStats[a.strategy]?.backtest_summary?.['# Trades'] || 0) -
            (strategiesStats[b.strategy]?.backtest_summary?.['# Trades'] || 0)
          );
        case 'Trades_desc':
          return (
            (strategiesStats[b.strategy]?.backtest_summary?.['# Trades'] || 0) -
            (strategiesStats[a.strategy]?.backtest_summary?.['# Trades'] || 0)
          );
        default:
          return 0;
      }
    });

    return indexedStrategies.map((item) => item.strategy);
  }, [availableStrategies, sortOption, strategiesStats]);

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <div className='flex flex-col gap-[100px] mt-[40px] px-[20px]'>
          <Typography variant='h3'>Доступные стратегии</Typography>
          {/* <Loading /> */}
        </div>
      </ThemeProvider>
    );
  }

  if (error) {
    return (
      <ThemeProvider theme={theme}>
        <div className='flex flex-col gap-[100px] mt-[40px] px-[20px]'>
          <Typography variant='h3'>Доступные стратегии</Typography>
          <Error message='Не удалось загрузить стратегии.' />
        </div>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <div className='flex flex-col gap-[100px] mt-[40px] px-[20px]'>
        <Typography variant='h3'>Доступные стратегии</Typography>

        <div className='flex flex-col gap-[60px] first:gap-[0px]'>
          <SortSelect
            sortOption={sortOption}
            handleSortChange={handleSortChange}
          />
          {sortedStrategies.map((strategy) => (
            <StrategyCard
              key={strategy}
              strategy={strategy}
              stats={strategiesStats[strategy]}
              plotUrl={plots[strategy]}
            />
          ))}
        </div>
      </div>
    </ThemeProvider>
  );
};

export default App;
