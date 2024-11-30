import { useEffect, useState, useMemo } from 'react';
import axios from 'axios';
import './App.css';
import { URL } from './web-config';
import Typography from '@mui/material/Typography';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import StrategyCard from './StrategyCard';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

const theme = createTheme({
  typography: {
    fontFamily: '"JetBrains Mono", "Arial", sans-serif',
  },
});

function App() {
  const [availableStrategies, setAvailableStrategies] = useState(null);
  const [strategiesStats, setStrategiesStats] = useState({});
  const [plots, setPlots] = useState({});
  const [sortOption, setSortOption] = useState('newness_desc');

  useEffect(() => {
    axios
      .get(`${URL}/strategies`)
      .then((response) =>
        setAvailableStrategies(response.data.available_strategies)
      )
      .catch((error) => console.log(error));
  }, []);

  useEffect(() => {
    if (availableStrategies) {
      const fetchStatsAndPlots = async () => {
        const stats = await Promise.all(
          availableStrategies.map((strategy) =>
            axios
              .get(
                `${URL}/run_strategy/result_for_strategy?strategy=${strategy}`
              )
              .then((response) => ({ strategy, data: response.data }))
              .catch(() => ({ strategy, data: null }))
          )
        );

        const statsObject = stats.reduce((acc, { strategy, data }) => {
          acc[strategy] = data;
          return acc;
        }, {});

        setStrategiesStats(statsObject);

        const plotResponses = await Promise.all(
          availableStrategies.map((strategy) =>
            axios
              .get(`${URL}/get_plot?strategy=${strategy}`)
              .then(() => ({
                strategy,
                plotUrl: `${URL}/get_plot?strategy=${strategy}`,
              }))
              .catch(() => ({ strategy, plotUrl: null }))
          )
        );

        const plotsObject = plotResponses.reduce(
          (acc, { strategy, plotUrl }) => {
            acc[strategy] = plotUrl;
            return acc;
          },
          {}
        );

        setPlots(plotsObject);
      };

      fetchStatsAndPlots();
    }
  }, [availableStrategies]);

  // Обработчик изменения опции сортировки
  const handleSortChange = (event) => {
    setSortOption(event.target.value);
  };

  // Используем useMemo для мемоизации отсортированного списка стратегий
  const sortedStrategies = useMemo(() => {
    if (!availableStrategies) return [];

    // Создаём копию массива для сортировки
    const strategiesCopy = [...availableStrategies];

    // Добавляем индекс для сортировки по новизне, если требуется
    const indexedStrategies = strategiesCopy.map((strategy, index) => ({
      strategy,
      index, // исходный индекс для сортировки по новизне
    }));

    // Определяем функцию сортировки в зависимости от выбранной опции
    indexedStrategies.sort((a, b) => {
      switch (sortOption) {
        case 'newness_asc':
          return a.index - b.index; // Старые сначала
        case 'newness_desc':
          return b.index - a.index; // Новые сначала
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

    // Возвращаем отсортированные имена стратегий
    return indexedStrategies.map((item) => item.strategy);
  }, [availableStrategies, sortOption, strategiesStats]);

  const handleDeleteStrategy = (deletedStrategy) => {
    setAvailableStrategies((prevStrategies) =>
      prevStrategies.filter((strategy) => strategy !== deletedStrategy)
    );
  };

  return (
    <ThemeProvider theme={theme}>
      <div className='flex flex-col gap-[100px] mt-[40px] px-[20px]'>
        <Typography variant='h3'>Доступные стратегии</Typography>

        <div className='flex flex-col gap-[60px] first:gap-[0px]'>
          <FormControl variant='outlined' sx={{ minWidth: 200 }}>
            <InputLabel id='sort-select-label'>Сортировка</InputLabel>
            <Select
              labelId='sort-select-label'
              id='sort-select'
              value={sortOption}
              onChange={handleSortChange}
              label='Сортировка'
            >
              <MenuItem value='newness_asc'>Новизна: Старые → Новые</MenuItem>
              <MenuItem value='newness_desc'>Новизна: Новые → Старые</MenuItem>
              <MenuItem value='SQN_asc'>SQN: Низкий → Высокий</MenuItem>
              <MenuItem value='SQN_desc'>SQN: Высокий → Низкий</MenuItem>
              <MenuItem value='Trades_asc'>Trades: Меньше → Больше</MenuItem>
              <MenuItem value='Trades_desc'>Trades: Больше → Меньше</MenuItem>
            </Select>
          </FormControl>
          {sortedStrategies &&
            sortedStrategies.map((strategy) => (
              <StrategyCard
                key={strategy}
                strategy={strategy}
                stats={strategiesStats[strategy]}
                plotUrl={plots[strategy]}
                onDelete={handleDeleteStrategy} // Передаем обработчик удаления
              />
            ))}
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;
