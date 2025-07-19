
import React, { useState } from 'react';
import { Bot, Play, AlertCircle, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { createCustomPlaylist, getAuthUrl } from '../services/api';

const CustomTab = ({ isAuthenticated }) => {
  const [userPrompt, setUserPrompt] = useState('');
  const [numSongs, setNumSongs] = useState(25);
  const [language, setLanguage] = useState('Auto-detect');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const languages = [
    'Auto-detect', 'English', 'Spanish', 'French', 'German', 'Italian',
    'Portuguese', 'Turkish', 'Japanese', 'Korean', 'Arabic', 'Hindi'
  ];

  const examples = [
    ['Cozy coffee shop atmosphere with indie and acoustic vibes', 20, 'English'],
    ['Epic workout motivation with high-energy electronic beats', 30, 'English'],
    ['Romantic dinner background music with smooth jazz and soul', 15, 'English'],
    ['Deep focus music for coding and productivity sessions', 40, 'English'],
    ['Driving at night through the city with synthwave vibes', 25, 'English'],
    ['Sabah rutini için neşeli ve enerjik Türkçe şarkılar', 25, 'Turkish']
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!userPrompt.trim() || userPrompt.length < 5) {
      toast.error('Please provide a detailed description of your desired playlist!');
      return;
    }

    if (!isAuthenticated) {
      try {
        const data = await getAuthUrl();
        window.open(data.auth_url, '_blank');
        toast.error('Please authenticate with Spotify first');
      } catch (error) {
        toast.error('Please authenticate with Spotify first');
      }
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const response = await createCustomPlaylist(userPrompt, numSongs, language);
      setResult(response);
      toast.success('Custom playlist created successfully!');
    } catch (error) {
      if (error.response?.data?.auth_needed) {
        toast.error('Authentication expired. Please re-authenticate.');
      } else {
        toast.error(error.response?.data?.error || 'Failed to create playlist');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="card">
        <h3 className="text-2xl font-bold mb-4 flex items-center">
          <Bot className="w-6 h-6 mr-2" />
          AI-Powered Custom Playlists
        </h3>
        <p className="text-gray-300 mb-6">
          Describe any playlist concept and let Elena's AI create the perfect tracklist
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              🎯 Describe your playlist concept:
            </label>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="Examples: 'Epic road trip through mountains' • 'Cozy coffee shop atmosphere' • 'Intense workout motivation' • 'Late night coding session'"
              className="input-modern w-full h-32 resize-none"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                🎵 Number of Songs
              </label>
              <input
                type="range"
                min="10"
                max="50"
                step="5"
                value={numSongs}
                onChange={(e) => setNumSongs(parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-400 mt-1">
                <span>10</span>
                <span className="font-medium text-white">{numSongs}</span>
                <span>50</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                🌍 Music Language (Optional)
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input-modern w-full"
              >
                {languages.map((lang) => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
            </div>
          </div>
          
          <button
            type="submit"
            disabled={isLoading || !userPrompt.trim() || userPrompt.length < 5}
            className="btn-primary w-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-black border-t-transparent mr-2"></div>
                Generating AI Playlist...
              </>
            ) : (
              <>
                <Play className="w-5 h-5 mr-2" />
                🎵 Generate AI Playlist
              </>
            )}
          </button>
        </form>
        
        {!isAuthenticated && (
          <div className="mt-4 p-4 bg-yellow-900 border border-yellow-700 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5 mr-3 flex-shrink-0" />
            <p className="text-yellow-200 text-sm">
              Please authenticate with Spotify above to generate playlists.
            </p>
          </div>
        )}
      </div>

      {result && (
        <div className="card">
          <h4 className="text-xl font-bold text-green-400 mb-4">
            🎧 {result.playlist.playlist_name}
          </h4>
          
          <div className="space-y-4">
            <div>
              <p className="text-gray-300">
                <strong>AI Generated Concept:</strong> {result.playlist_concept.description}
              </p>
              <p className="text-gray-300">
                <strong>Language:</strong> {language}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <strong className="text-white">Tracks:</strong>
                <p className="text-gray-300">{result.playlist.track_count} songs</p>
              </div>
              <div>
                <strong className="text-white">Genres:</strong>
                <p className="text-gray-300">{result.playlist_concept.genres.join(', ')}</p>
              </div>
              <div>
                <strong className="text-white">Themes:</strong>
                <p className="text-gray-300">{result.playlist_concept.themes?.join(', ') || 'Various'}</p>
              </div>
            </div>
            
            <div>
              <strong className="text-white">Sample Tracks:</strong>
              <ul className="list-disc list-inside text-gray-300 mt-2">
                {result.playlist.sample_tracks.map((track, index) => (
                  <li key={index}>{track}</li>
                ))}
              </ul>
            </div>
            
            <a
              href={result.playlist.playlist_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary inline-flex items-center"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              🎧 Open in Spotify
            </a>
          </div>
        </div>
      )}
      
      {/* Examples */}
      <div className="card bg-gray-800">
        <h4 className="text-lg font-semibold mb-4">💡 Try These Playlist Concepts:</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => {
                setUserPrompt(example[0]);
                setNumSongs(example[1]);
                setLanguage(example[2]);
              }}
              className="text-left p-3 rounded bg-gray-700 hover:bg-gray-600 transition-colors text-sm"
            >
              <span className="text-gray-300">"{example[0]}"</span>
              <div className="flex justify-between text-gray-500 text-xs mt-1">
                <span>{example[1]} songs</span>
                <span>{example[2]}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CustomTab;
