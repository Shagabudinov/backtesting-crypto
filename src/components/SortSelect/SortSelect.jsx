import React from 'react';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

const SortSelect = ({ sortOption, handleSortChange }) => {
  return (
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
  );
};

export default SortSelect;
