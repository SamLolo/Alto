// src/components/Queue.js
import React, { useState } from 'react';

const Queue = ({ queue, onSongSelect }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className="queue">
      <button onClick={toggleCollapse}>
        {isCollapsed ? 'Show Queue' : 'Hide Queue'}
      </button>

      {!isCollapsed && (
        <ul>
          {queue.map((song, index) => (
            <li key={index} onClick={() => onSongSelect(song)}>
              <img src={song.albumArt} alt="Album Art" width="40" />
              {song.title}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default Queue;