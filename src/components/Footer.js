import React from 'react';
import { Heart } from 'lucide-react';

const Footer = () => {
  return (
    <div className="mt-16 text-center">
      <div className="card">
        <div className="border-t border-gray-700 pt-8">
          <div className="flex items-center justify-center mb-3">
            <Heart className="w-5 h-5 text-red-400 mr-2" />
            <h3 className="text-lg font-semibold">👨‍💻 Created by Han</h3>
          </div>
          <p className="text-gray-300 mb-2">
            <strong>Elena - Your DJ</strong> © 2024 • Built with ❤️ for Elena • Powered by AI & Music
          </p>
          <p className="text-gray-400 text-sm italic">
            A sophisticated music companion that transforms emotions into perfect playlists
          </p>
        </div>
      </div>
    </div>
  );
};

export default Footer;
