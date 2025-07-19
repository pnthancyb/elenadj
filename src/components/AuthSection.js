
import React, { useState } from 'react';
import { ExternalLink, CheckCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { getAuthUrl, authenticate } from '../services/api';

const AuthSection = ({ isAuthenticated, setIsAuthenticated }) => {
  const [authUrl, setAuthUrl] = useState('');
  const [callbackUrl, setCallbackUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [redirectUri, setRedirectUri] = useState('');

  const handleGetAuthUrl = async () => {
    try {
      setLoading(true);
      const response = await getAuthUrl();
      setAuthUrl(response.auth_url);
      setRedirectUri(response.redirect_uri);
      window.open(response.auth_url, '_blank');
      toast.success('Opening Spotify authentication...');
    } catch (error) {
      toast.error('Failed to get authentication URL');
    } finally {
      setLoading(false);
    }
  };

  const handleAuthenticate = async () => {
    if (!callbackUrl.trim()) {
      toast.error('Please paste the callback URL');
      return;
    }

    try {
      setLoading(true);
      const response = await authenticate(callbackUrl);
      
      if (response.success) {
        setIsAuthenticated(true);
        toast.success(response.message);
        setCallbackUrl('');
      } else {
        toast.error(response.message);
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  if (isAuthenticated) {
    return (
      <div className="card card-auth">
        <div className="flex items-center justify-center text-green-400 mb-4">
          <CheckCircle className="w-8 h-8 mr-3" />
          <div>
            <h3 className="text-xl font-semibold">Spotify Connected</h3>
            <p className="text-gray-400">You can now create personalized playlists!</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-800">
        <h2 className="text-2xl font-bold mb-4">🚀 Quick Setup Guide</h2>
        <div className="space-y-3 text-gray-300">
          <p><strong>Essential API Keys</strong> (Add to Secrets 🔒):</p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li><code className="bg-gray-800 px-2 py-1 rounded">GROQ_API_KEY</code> - Get free at{' '}
              <a href="https://console.groq.com/" target="_blank" rel="noopener noreferrer" 
                 className="text-blue-400 hover:text-blue-300 underline">
                console.groq.com
              </a>
            </li>
            <li><code className="bg-gray-800 px-2 py-1 rounded">SPOTIFY_CLIENT_ID</code> & <code className="bg-gray-800 px-2 py-1 rounded">SPOTIFY_CLIENT_SECRET</code> - Get at{' '}
              <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener noreferrer"
                 className="text-blue-400 hover:text-blue-300 underline">
                developer.spotify.com
              </a>
            </li>
          </ul>
          {redirectUri && (
            <p className="mt-4 p-3 bg-yellow-900/30 border border-yellow-600 rounded-lg">
              <strong>Important:</strong> Add this redirect URI to your Spotify app settings: 
              <code className="block mt-1 bg-gray-800 px-2 py-1 rounded text-sm">{redirectUri}</code>
            </p>
          )}
        </div>
      </div>

      <div className="card card-auth">
        <div className="flex items-center mb-4">
          <ExternalLink className="w-6 h-6 mr-3 text-green-400" />
          <h3 className="text-xl font-semibold">Spotify Authentication</h3>
        </div>
        <p className="text-gray-400 mb-6">Connect your Spotify account to start creating personalized playlists</p>
        
        <div className="space-y-4">
          <button
            onClick={handleGetAuthUrl}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-black mr-2"></div>
            ) : (
              <ExternalLink className="w-5 h-5 mr-2" />
            )}
            Connect with Spotify
          </button>
          
          {authUrl && (
            <div className="space-y-3">
              <div className="flex items-start space-x-2 text-sm text-yellow-400">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <p>After authorizing, copy the callback URL and paste it below:</p>
              </div>
              
              <textarea
                value={callbackUrl}
                onChange={(e) => setCallbackUrl(e.target.value)}
                placeholder="Paste the Spotify callback URL here..."
                className="input-modern w-full h-24 resize-none"
              />
              
              <button
                onClick={handleAuthenticate}
                disabled={loading || !callbackUrl.trim()}
                className="btn-primary w-full"
              >
                {loading ? 'Authenticating...' : 'Complete Authentication'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthSection;
