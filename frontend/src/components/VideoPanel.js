import React, { useEffect, useRef } from 'react';
import io from 'socket.io-client';

const VideoPanel = ({ token }) => {
  const videoRef = useRef(null);

  useEffect(() => {
    const socket = io('http://localhost:5000', {
      extraHeaders: { Authorization: `Bearer ${token}` }
    });

    socket.on('video_feed', (data) => {
      const img = document.getElementById('video-frame');
      img.src = `data:image/jpeg;base64,${data.frame}`;
    });

    return () => socket.disconnect();
  }, [token]);

  return (
    <div className="video-grid">
      <img id="video-frame" ref={videoRef} alt="监控画面" />
    </div>
  );
};