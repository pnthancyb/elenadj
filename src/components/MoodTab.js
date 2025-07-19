import React, { useState } from 'react';
import { Heart, Play, AlertCircle, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { createMoodPlaylist, getAuthUrl } from '../services/api';

const MoodTab = ({ isAuthenticated }) => {
  const [moodText, setMoodText] = useState('');
  const [language, setLanguage] = useState('English');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);

  const languages = [
    'English', 'Spanish', 'French', 'German', 'Italian',
    'Portuguese', 'Turkish', 'Japanese', 'Korean', 'Arabic', 'Hindi'
  ];

  const exampleMoods = [
    ['Feeling nostalgic and dreamy, like watching old movies on a rainy day', 'English'],
    ['Energetic and ready to conquer the world, need pump-up music', 'English'],
    ['Stresli ama pozitif kalmaya çalışıyorum, motivasyona ihtiyacım var', 'Turkish'],
    ['Mélancolique et introspectif, besoin de musique douce', 'French'],
    ['Peaceful and contemplative, seeking zen and mindfulness', 'English'],
    ['Romantic and passionate, thinking about someone special', 'Spanish']
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!moodText.trim()) {
      toast.error('Please describe how you\'re feeling today!');
      return;
    }

    if (!isAuthenticated) {
      try {
        const data = await getAuthUrl();
        window.open(data.auth_url, '_blank');
        toast.error('Please authenticate with Spotify first');
      } catch {
        toast.error('Please authenticate with Spotify first');
      }
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
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
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="card">
        <h3 className="text-2xl font-bold mb-4 flex items-center">
          <Heart className="w-6 h-6 mr-2" />
          Emotion-Driven Playlists
        </h3>
        <p className="text-gray-300 mb-6">
          Describe your current feelings and let Elena create the perfect soundtrack
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                💭 How are you feeling today?
              </label>
              <textarea
                value={moodText}
                onChange={(e) => setMoodText(e.target.value)}
                placeholder="Examples: 'nostalgic and dreamy' • 'energetic and motivated' • 'peaceful Sunday vibes' • 'melancholic but hopeful'"
                className="input-modern w-full h-32 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                🌍 Music Language
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
            disabled={isLoading || !moodText.trim()}
            className="btn-primary w-full flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-black border-t-transparent mr-2"></div>
                Generating Mood Playlist...
              </>
            ) : (
              <>
                <Play className="w-5 h-5 mr-2" />
                🎵 Generate Mood Playlist
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
                <strong>Your Mood:</strong> {result.mood_analysis.mood_description}
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
                <p className="text-gray-300">{result.mood_analysis.genres.join(', ')}</p>
              </div>
              <div>
                <strong className="text-white">Energy Level:</strong>
                <p className="text-gray-300">{result.mood_analysis.energy_level}/10</p>
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
        <h4 className="text-lg font-semibold mb-4">💡 Try These Mood Examples:</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {exampleMoods.map((example, index) => (
            <button
              key={index}
              onClick={() => {
                setMoodText(example[0]);
                setLanguage(example[1]);
              }}
              className="text-left p-3 rounded bg-gray-700 hover:bg-gray-600 transition-colors text-sm"
            >
              <span className="text-gray-300">"{example[0]}"</span>
              <span className="block text-gray-500 text-xs mt-1">{example[1]}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MoodTab;
