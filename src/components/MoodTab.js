
import React, { useState } from 'react';
import { Play, AlertCircle, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { createMoodPlaylist, getAuthUrl } from '../services/api';

const MoodTab = ({ isAuthenticated }) => {
  const [moodText, setMoodText] = useState('');
  const [language, setLanguage] = useState('English');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const languages = [
    'English', 'Spanish', 'French', 'German', 'Italian', 
    'Portuguese', 'Turkish', 'Japanese', 'Korean', 'Arabic', 'Hindi'
  ];

  const examples = [
    { mood: "Feeling nostalgic and dreamy, like watching old movies on a rainy day", lang: "English" },
    { mood: "Energetic and ready to conquer the world, need pump-up music", lang: "English" },
    { mood: "Stresli ama pozitif kalmaya çalışıyorum, motivasyona ihtiyacım var", lang: "Turkish" },
    { mood: "Mélancolique et introspectif, besoin de musique douce", lang: "French" },
    { mood: "Peaceful and contemplative, seeking zen and mindfulness", lang: "English" },
    { mood: "Romantic and passionate, thinking about someone special", lang: "Spanish" },
    { mood: "Confident and rebellious, feeling like breaking some rules", lang: "English" },
    { mood: "Tired but hopeful, end of a long day but optimistic", lang: "English" }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!moodText.trim()) {
      toast.error('Please describe how you\'re feeling today!');
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
      const response = await createMoodPlaylist(moodText, language);
      setResult(response);
      toast.success('Mood playlist created successfully!');
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
    setMoodText(example.mood);
    setLanguage(example.lang);
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center mb-4">
          <Brain className="w-6 h-6 mr-3 text-purple-400" />
          <h2 className="text-2xl font-bold">Emotion-Driven Playlists</h2>
        </div>
        <p className="text-gray-400 mb-6">Describe your current feelings and let Elena create the perfect soundtrack</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-3">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                💭 How are you feeling today?
              </label>
              <textarea
                value={moodText}
                onChange={(e) => setMoodText(e.target.value)}
                placeholder="Examples: 'nostalgic and dreamy' • 'energetic and motivated' • 'peaceful Sunday vibes' • 'melancholic but hopeful'"
                className="input-modern w-full h-32 resize-none"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                🌍 Music Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input-modern w-full h-32"
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
                <span>Creating Your Mood Playlist...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Generate Mood Playlist</span>
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
        <div className="card bg-gradient-to-br from-green-900/20 to-blue-900/20 border-green-800">
          <h3 className="text-xl font-bold text-green-400 mb-4">
            🎧 {result.playlist.playlist_name} is ready!
          </h3>
          
          <div className="space-y-4">
            <div>
              <p className="text-gray-300">
                <strong>🔮 Your Mood:</strong> {result.mood_analysis.mood_description}
              </p>
              <p className="text-gray-300">
                <strong>🌍 Language:</strong> {language}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-gray-300 mb-2"><strong>📊 Playlist Details:</strong></p>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• {result.playlist.track_count} carefully selected tracks</li>
                  <li>• Genres: {result.mood_analysis.genres.join(', ')}</li>
                  <li>• Energy Level: {result.mood_analysis.energy_level}/10</li>
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
        <h3 className="text-lg font-semibold mb-4">💡 Try These Mood Examples:</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              className="text-left p-3 bg-gray-900 hover:bg-gray-800 border border-gray-700 rounded-lg transition-colors text-sm"
            >
              <div className="text-gray-300">{example.mood}</div>
              <div className="text-gray-500 text-xs mt-1">{example.lang}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MoodTab;
