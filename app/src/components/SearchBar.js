// src/components/SearchBar.js
import React, { useState } from 'react';
import axios from 'axios';

const SearchBar = ({ onSearchResult }) => {
  const [query, setQuery] = useState('');

  const handleSearch = async () => {
    // Replace with an actual API call or mock data
    const response = await axios.get(`https://api.example.com/search?q=${query}`);
    onSearchResult(response.data);
  };

  return (
    <div className="search-bar">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search for a song..."
      />
      <button onClick={handleSearch}>Search</button>
    </div>
  );
};

export default SearchBar;