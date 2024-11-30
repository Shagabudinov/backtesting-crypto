import { useEffect, useState } from 'react';
import {
  fetchAvailableStrategies,
  fetchStrategyStats,
  fetchStrategyPlot,
} from '../services/api';

const useFetchStrategies = () => {
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [strategiesStats, setStrategiesStats] = useState({});
  const [plots, setPlots] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        const strategiesResponse = await fetchAvailableStrategies();
        const strategies = strategiesResponse.data.available_strategies;
        setAvailableStrategies(strategies);

        const statsPromises = strategies.map((strategy) =>
          fetchStrategyStats(strategy)
            .then((res) => ({ strategy, data: res.data }))
            .catch(() => ({ strategy, data: null }))
        );

        const statsResults = await Promise.all(statsPromises);
        const statsObject = statsResults.reduce((acc, { strategy, data }) => {
          acc[strategy] = data;
          return acc;
        }, {});
        setStrategiesStats(statsObject);

        const plotPromises = strategies.map((strategy) =>
          fetchStrategyPlot(strategy)
            .then(() => ({
              strategy,
              plotUrl: `${URL}/get_plot?strategy=${strategy}`,
            }))
            .catch(() => ({ strategy, plotUrl: null }))
        );

        const plotResults = await Promise.all(plotPromises);
        const plotsObject = plotResults.reduce((acc, { strategy, plotUrl }) => {
          acc[strategy] = plotUrl;
          return acc;
        }, {});
        setPlots(plotsObject);

        setLoading(false);
      } catch (err) {
        console.error(err);
        setError(err);
        setLoading(false);
      }
    };

    fetchAllData();
  }, []);

  return { availableStrategies, strategiesStats, plots, loading, error };
};

export default useFetchStrategies;
