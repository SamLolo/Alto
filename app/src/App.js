// src/App.js
import React, { useState } from 'react';
import Player from './components/Player';
import Queue from './components/Queue';
import SearchBar from './components/SearchBar';

const App = () => {
  const [queue, setQueue] = useState([]);
  const [currentSong, setCurrentSong] = useState(null);

  const handleSearchResult = (songs) => {
    setQueue((prevQueue) => [...prevQueue, ...songs]);
  };

  const handlePlayPause = () => {
    // Manage play/pause state here (optional, depending on design)
  };

  const handleSkipForward = () => {
    const nextSong = queue[1]; // skip to next song in queue
    setQueue(queue.slice(1));
    setCurrentSong(nextSong);
  };

  const handleSkipBackward = () => {
    const previousSong = queue[queue.length - 2]; // skip to previous song
    setQueue([previousSong, ...queue.slice(0, -1)]);
    setCurrentSong(previousSong);
  };

  const handleSongSelect = (song) => {
    setQueue([song, ...queue]);
    setCurrentSong(song);
  };

  return (
    <div className="app">
      <SearchBar onSearchResult={handleSearchResult} />
      <Player
        currentSong={currentSong}
        onPlayPause={handlePlayPause}
        onSkipForward={handleSkipForward}
        onSkipBackward={handleSkipBackward}
      />
      <Queue queue={queue} onSongSelect={handleSongSelect} />
    </div>
  );
};

export default App;
