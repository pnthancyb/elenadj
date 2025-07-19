
import React, { useState } from 'react';
import { Bot, Play, AlertCircle, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { createCustomPlaylist, getAuthUrl } from '../services/api';

const CustomTab = ({ isAuthenticated }) => {
  const [userPrompt, setUserPrompt] = useState('');
  const [numSongs, setNumSongs] = useState(25);
  const [language, setLanguage] = useState('Auto-detect');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const languages = [
    'Auto-detect', 'English', 'Spanish', 'French', 'German', 'Italian', 
    'Portuguese', 'Turkish', 'Japanese', 'Korean', 'Arabic', 'Hindi'
  ];

  const examples = [
    { prompt: "Cozy coffee shop atmosphere with indie and acoustic vibes", songs: 20, lang: "English" },
    { prompt: "Epic workout motivation with high-energy electronic beats", songs: 30, lang: "English" },
    { prompt: "Romantic dinner background music with smooth jazz and soul", songs: 15, lang: "English" },
    { prompt: "Deep focus music for coding and productivity sessions", songs: 40, lang: "English" },
    { prompt: "Driving at night through the city with synthwave vibes", songs: 25, lang: "English" },
    { prompt: "Sabah rutini için neşeli ve enerjik Türkçe şarkılar", songs: 25, lang: "Turkish" },
    { prompt: "Relaxing spa and meditation soundscape", songs: 35, lang: "English" },
    { prompt: "90s nostalgia trip with the best hits from that decade", songs: 45, lang: "English" }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!userPrompt.trim() || userPrompt.trim().length < 5) {
      toast.error('Please provide a detailed description of your desired playlist!');
      return;
    }

    if (!isAuthenticated) {
      try {
        const response = await getAuthUrl();
        window.open(response.auth_url, '_blank');
        toast.error('Please authenticate with Spotify first');
      } catch (error) {
        toast.error('Authentication required');
      }
      return;
    }

    try {
      setLoading(true);
      setResult(null);
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
      setLoading(false);
    }
  };

  const handleExampleClick = (example) => {
    setUserPrompt(example.prompt);
    setNumSongs(example.songs);
    setLanguage(example.lang);
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center mb-4">
          <Bot className="w-6 h-6 mr-3 text-blue-400" />
          <h2 className="text-2xl font-bold">AI-Powered Custom Playlists</h2>
        </div>
        <p className="text-gray-400 mb-6">Describe any playlist concept and let Elena's AI create the perfect tracklist</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              🎯 Describe your playlist concept:
            </label>
            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              placeholder="Examples: 'Epic road trip through mountains' • 'Cozy coffee shop atmosphere' • 'Intense workout motivation' • 'Late night coding session'"
              className="input-modern w-full h-32 resize-none"
              required
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
                onChange={(e) => setNumSongs(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-sm text-gray-400 mt-1">
                <span>10</span>
                <span className="font-semibold text-white">{numSongs}</span>
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
                  <option key={lang} value={lang} className="bg-gray-800">
                    {lang}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <button
            type="submit"
            disabled={loading || !isAuthenticated}
            className="btn-primary w-full flex items-center justify-center space-x-2 text-lg py-4"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-black"></div>
                <span>Creating Your AI Playlist...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Generate AI Playlist</span>
              </>
            )}
          </button>
        </form>

        {!isAuthenticated && (
          <div className="mt-4 p-3 bg-yellow-900/30 border border-yellow-600 rounded-lg flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
            <p className="text-yellow-200 text-sm">
              Please authenticate with Spotify first to create playlists.
            </p>
          </div>
        )}
      </div>

      {result && (
        <div className="card bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-800">
          <h3 className="text-xl font-bold text-blue-400 mb-4">
            🎧 {result.playlist.playlist_name} is ready!
          </h3>
          
          <div className="space-y-4">
            <div>
              <p className="text-gray-300">
                <strong>🤖 AI Generated Concept:</strong> {result.playlist_concept.description}
              </p>
              <p className="text-gray-300">
                <strong>🌍 Language:</strong> {language}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-gray-300 mb-2"><strong>📊 Playlist Details:</strong></p>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• {result.playlist.track_count} tracks</li>
                  <li>• Genres: {result.playlist_concept.genres.join(', ')}</li>
                  <li>• Themes: {result.playlist_concept.themes?.join(', ') || 'N/A'}</li>
                </ul>
              </div>
              
              <div>
                <p className="text-gray-300 mb-2"><strong>🎵 Sample Tracks:</strong></p>
                <ul className="text-sm text-gray-400 space-y-1">
                  {result.playlist.sample_tracks.map((track, index) => (
                    <li key={index}>• {track}</li>
                  ))}
                </ul>
              </div>
            </div>
            
            <a
              href={result.playlist.playlist_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary inline-flex items-center space-x-2"
            >
              <ExternalLink className="w-5 h-5" />
              <span>🎧 Open in Spotify</span>
            </a>
          </div>
        </div>
      )}

      <div className="card bg-gray-800/50">
        <h3 className="text-lg font-semibold mb-4">💡 Try These Playlist Concepts:</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              className="text-left p-3 bg-gray-900 hover:bg-gray-800 border border-gray-700 rounded-lg transition-colors text-sm"
            >
              <div className="text-gray-300">{example.prompt}</div>
              <div className="text-gray-500 text-xs mt-1">
                {example.songs} songs • {example.lang}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CustomTab;
