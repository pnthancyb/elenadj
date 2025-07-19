
import React from 'react';
import { Heart } from 'lucide-react';

const Footer = () => {
  return (
    <div className="card text-center bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="flex items-center justify-center mb-3">
        <Heart className="w-5 h-5 text-red-400 mr-2" />
        <h3 className="text-lg font-semibold">Created by Han</h3>
      </div>
      <p className="text-gray-400 mb-2">
        <strong>Elena - Your DJ</strong> © 2024 • Built with ❤️ for Elena • Powered by AI & Music
      </p>
      <p className="text-gray-500 text-sm italic">
        A sophisticated music companion that transforms emotions into perfect playlists
      </p>
    </div>
  );
};

export default Footer;
