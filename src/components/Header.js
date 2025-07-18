import React from 'react';
import { Music } from 'lucide-react';

const Header = () => {
  return (
    <div className="text-center mb-12">
      <div className="card mb-8 bg-gradient-to-br from-gray-900 to-gray-800 border-2 border-gray-700 py-8">
        <div className="flex items-center justify-center mb-6">
          <Music className="w-12 h-12 mr-4 text-white" />
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            Elena - Your DJ
          </h1>
        </div>
        <p className="text-xl text-gray-300 mb-2">AI-Powered Spotify Playlist Generator</p>
        <p className="text-gray-400">Transform your emotions and ideas into perfect playlists with advanced AI</p>
      </div>
    </div>
  );
};

export default Header;
