
import React from 'react';
import { Music } from 'lucide-react';

const Header = () => {
  return (
    <div className="card text-center py-8 bg-gradient-to-br from-gray-900 to-gray-800 border-2 border-gray-700">
      <div className="flex items-center justify-center mb-4">
        <Music className="w-12 h-12 text-white mr-3" />
        <h1 className="text-5xl font-bold text-white">Elena - Your DJ</h1>
      </div>
      <p className="text-xl text-gray-300 mb-2">AI-Powered Spotify Playlist Generator</p>
      <p className="text-gray-400">Transform your emotions and ideas into perfect playlists with advanced AI</p>
    </div>
  );
};

export default Header;
