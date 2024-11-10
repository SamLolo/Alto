// src/components/Player.js
import React, { useState, useRef, useEffect } from 'react';
import { FaPlay, FaPause, FaStepForward, FaStepBackward } from 'react-icons/fa';

const Player = ({ currentSong, onPlayPause, onSkipForward, onSkipBackward }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    if (isPlaying) {
      audioRef.current.play();
    } else {
      audioRef.current.pause();
    }
  }, [isPlaying]);

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying);
    onPlayPause();
  };

  return (
    <div className="player">
      <div className="album-art">
        {currentSong ? (
          <img src={currentSong.albumArt} alt="Album Art" />
        ) : (
          <div>No song</div>
        )}
      </div>
      
      <div className="controls">
        <button onClick={onSkipBackward}><FaStepBackward /></button>
        <button onClick={togglePlayPause}>
          {isPlaying ? <FaPause /> : <FaPlay />}
        </button>
        <button onClick={onSkipForward}><FaStepForward /></button>
      </div>

      <div className="song-duration">
        {currentSong && (
          <input
            type="range"
            min="0"
            max={currentSong.duration}
            step="1"
            value={audioRef.current?.currentTime || 0}
            onChange={(e) => {
              audioRef.current.currentTime = e.target.value;
            }}
          />
        )}
      </div>
    </div>
  );
};

export default Player;