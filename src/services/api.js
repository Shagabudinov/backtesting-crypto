import axios from 'axios';
import { URL } from '../web-config';

// Fetch available strategies
export const fetchAvailableStrategies = () => {
  return axios.get(`${URL}/strategies`);
};

// Fetch stats for a specific strategy
export const fetchStrategyStats = (strategy) => {
  return axios.get(`${URL}/run_strategy/result_for_strategy`, {
    params: { strategy },
  });
};

// Fetch plot for a specific strategy
export const fetchStrategyPlot = (strategy) => {
  return axios.get(`${URL}/get_plot`, {
    params: { strategy },
  });
};

// Fetch distribution plot for a strategy
export const fetchDistributionPlot = (strategy) => {
  return axios.get(`${URL}/year-graph/result_for_strategy`, {
    params: { strategy },
  });
};
