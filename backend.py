#!/usr/bin/env python3
"""
Elena - Your DJ - Flask Backend API
"""

import json
import os
import re
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from groq import Groq
from datetime import datetime
import logging
import sys
import urllib.parse
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import unicodedata

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

import os

# Check if build folder exists, if not use a default
static_folder = 'build' if os.path.exists('build') else 'public'
app = Flask(__name__, static_folder=static_folder, static_url_path='/')
CORS(app)

class ElenaDJ:
    def __init__(self):
        """Initialize Elena - Your DJ with optimized configuration"""
        self.groq_client = None
        self.spotify_clients = {}
        self.spotify_auths = {}
        self.redirect_uri = None
        self.setup_apis()

    def clean_credential(self, credential: str) -> str:
        """Clean credential string from unwanted characters and encoding issues"""
        if not credential:
            return ""
        
        # Remove any non-ASCII characters and normalize
        credential = credential.encode('ascii', errors='ignore').decode('ascii')
        
        # Remove common unwanted characters
        unwanted_chars = ['…', '​', '\u200b', '\u200c', '\u200d', '\ufeff']
        for char in unwanted_chars:
            credential = credential.replace(char, '')
        
        # Strip whitespace and newlines
        credential = credential.strip().replace('\n', '').replace('\r', '')
        
        # Remove any trailing dots or special characters that might be artifacts
        credential = re.sub(r'[^\w\-]$', '', credential)
        
        return credential

    def setup_apis(self):
        """Setup APIs with environment support and enhanced credential cleaning"""
        try:
            # Get API keys with enhanced cleaning
            groq_api_key = self.clean_credential(os.getenv('GROQ_API_KEY', ''))
            self.spotify_client_id = self.clean_credential(os.getenv('SPOTIFY_CLIENT_ID', ''))
            self.spotify_client_secret = self.clean_credential(os.getenv('SPOTIFY_CLIENT_SECRET', ''))

            # Validation
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            if not self.spotify_client_id or not self.spotify_client_secret:
                raise ValueError("Spotify credentials not found in environment")

            # Validate format
            if len(self.spotify_client_id) != 32 or not re.match(r'^[a-zA-Z0-9]+$', self.spotify_client_id):
                logger.warning(f"Spotify Client ID format seems incorrect: '{self.spotify_client_id}' (length: {len(self.spotify_client_id)})")
                raise ValueError("Spotify Client ID format is invalid")

            if len(self.spotify_client_secret) != 32 or not re.match(r'^[a-zA-Z0-9]+$', self.spotify_client_secret):
                logger.warning(f"Spotify Client Secret format seems incorrect (length: {len(self.spotify_client_secret)})")
                raise ValueError("Spotify Client Secret format is invalid")

            # Initialize Groq client
            self.groq_client = Groq(api_key=groq_api_key)

            # Setup Spotify OAuth
            self.redirect_uri = self.get_redirect_uri()
            logger.info(f"Using redirect URI: {self.redirect_uri}")
            logger.info(f"Using Spotify Client ID: {self.spotify_client_id[:8]}... (length: {len(self.spotify_client_id)})")
            logger.info(f"Spotify Client Secret length: {len(self.spotify_client_secret)}")

            logger.info("Elena - Your DJ APIs initialized successfully")

        except Exception as e:
            logger.error(f"API setup failed: {e}")
            raise

    def get_redirect_uri(self):
        """Get the correct redirect URI for current environment"""
        # First priority: Environment variable
        env_redirect = os.getenv('SPOTIFY_REDIRECT_URI')
        if env_redirect:
            return self.clean_credential(env_redirect)
        
        # Second priority: Local tunnel URL
        repl_url = os.getenv('REPL_URL')
        if repl_url:
            if not repl_url.startswith('https://'):
                repl_url = repl_url.replace('http://', 'https://')
            return f"{repl_url}/api/spotify-callback"
        
        # Third priority: Replit dev domain
        replit_domain = os.getenv('REPLIT_DEV_DOMAIN')
        if replit_domain:
            return f"https://{replit_domain}/api/spotify-callback"
        
        # Fallback: Local development
        return "http://127.0.0.1:5000/api/spotify-callback"

    def create_spotify_auth(self, session_id: str = "default") -> SpotifyOAuth:
        """Create Spotify OAuth object with proper encoding"""
        cache_dir = os.path.join(os.getcwd(), '.cache-spotify')

        try:
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f'spotify_token_{session_id}')
        except Exception as e:
            logger.warning(f"Could not set up cache directory: {e}")
            cache_path = None

        # Log the exact values being used (for debugging)
        logger.info(f"Creating SpotifyOAuth with:")
        logger.info(f"  Client ID: {self.spotify_client_id[:8]}... (len: {len(self.spotify_client_id)})")
        logger.info(f"  Client Secret: {'*' * min(8, len(self.spotify_client_secret))}... (len: {len(self.spotify_client_secret)})")
        logger.info(f"  Redirect URI: {self.redirect_uri}")

        # Ensure all parameters are properly encoded strings
        return SpotifyOAuth(
            client_id=str(self.spotify_client_id),
            client_secret=str(self.spotify_client_secret),
            redirect_uri=str(self.redirect_uri),
            scope='playlist-modify-public playlist-modify-private',
            cache_path=cache_path,
            show_dialog=True,
            open_browser=False
        )

    def get_auth_url(self, session_id: str = "default") -> str:
        """Get authorization URL with proper error handling"""
        try:
            if session_id not in self.spotify_auths:
                self.spotify_auths[session_id] = self.create_spotify_auth(session_id)
            
            auth_url = self.spotify_auths[session_id].get_authorize_url()
            logger.info(f"Generated auth URL: {auth_url[:100]}...")
            
            # Check if the URL contains any problematic characters
            if '…' in auth_url or '\u2026' in auth_url:
                logger.error("Auth URL contains ellipsis characters!")
                raise ValueError("Auth URL contains invalid characters")
                
            return auth_url
        except Exception as e:
            logger.error(f"Failed to generate auth URL: {e}")
            raise

    def authenticate_with_code(self, callback_url: str, session_id: str = "default") -> Tuple[bool, str]:
        """Authenticate using callback URL with improved error handling"""
        try:
            # Clean the callback URL
            callback_url = callback_url.encode('ascii', errors='ignore').decode('ascii')
            
            parsed_url = urllib.parse.urlparse(callback_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)

            if 'code' not in query_params:
                if 'error' in query_params:
                    error = query_params['error'][0]
                    error_description = query_params.get('error_description', [''])[0]
                    return False, f"Authentication failed: {error} - {error_description}"
                else:
                    return False, "No authorization code found in callback URL"

            code = query_params['code'][0]
            logger.info(f"Received auth code: {code[:10]}...")

            if session_id not in self.spotify_auths:
                self.spotify_auths[session_id] = self.create_spotify_auth(session_id)

            token_info = self.spotify_auths[session_id].get_access_token(code)

            if token_info:
                if isinstance(token_info, dict):
                    access_token = token_info.get('access_token')
                else:
                    access_token = token_info

                spotify_client = spotipy.Spotify(auth=access_token)
                user_info = spotify_client.current_user()
                user_id = user_info.get('id')
                display_name = user_info.get('display_name') or user_id

                self.spotify_clients[user_id] = spotify_client

                logger.info(f"Successfully authenticated user: {display_name}")
                return True, f"Successfully authenticated as {display_name}"
            else:
                return False, "Failed to exchange code for access token"

        except UnicodeEncodeError as e:
            logger.error(f"Unicode encoding error: {e}")
            return False, "Authentication failed due to character encoding issues. Please ensure your Spotify credentials are properly configured."
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False, f"Authentication error: {str(e)}"

    def get_authenticated_client(self, session_id: str = "default") -> Optional[spotipy.Spotify]:
        """Get authenticated Spotify client with better error handling"""
        for user_id, client in list(self.spotify_clients.items()):
            try:
                client.current_user()
                return client
            except Exception as e:
                logger.warning(f"Client for user {user_id} is invalid: {e}")
                del self.spotify_clients[user_id]

        if session_id in self.spotify_auths:
            try:
                auth = self.spotify_auths[session_id]
                token_info = auth.get_cached_token()
                if token_info:
                    if auth.is_token_expired(token_info):
                        token_info = auth.refresh_access_token(token_info['refresh_token'])

                    if token_info:
                        client = spotipy.Spotify(auth=token_info['access_token'])
                        user_info = client.current_user()
                        user_id = user_info.get('id')
                        self.spotify_clients[user_id] = client
                        return client
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")

        return None

    def is_authenticated(self, session_id: str = "default") -> bool:
        """Check if user is authenticated"""
        return self.get_authenticated_client(session_id) is not None

    def analyze_mood(self, text: str, language: str = "English") -> Dict:
        """Enhanced mood analysis with AI song recommendations"""
        if not text or len(text.strip()) < 3:
            return {"error": "Please describe your mood in a few words"}

        try:
            language_context = ""
            if language != "English":
                language_context = f" Focus on {language} music and popular artists from that region."

            prompt = f"""
            Analyze this mood: '{text}'{language_context}

            Return ONLY valid JSON with these keys:
            - "emotion": primary emotion (e.g., "melancholic", "energetic", "peaceful")
            - "themes": array of 2-3 themes (e.g., ["nostalgia", "chill"])
            - "genres": array of 4-6 SPECIFIC music genres (e.g., ["indie rock", "acoustic folk", "lo-fi hip hop"])
            - "energy_level": number 1-10
            - "mood_description": brief description
            - "language_preference": "{language}"
            - "recommended_songs": array of 20-25 specific song recommendations with format "Artist - Song Title"

            IMPORTANT: Recommend actual, real songs by popular artists that match the mood. Use well-known songs that are likely to be on Spotify.
            """

            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()

            mood_data = json.loads(content)
            required_keys = ['emotion', 'themes', 'genres', 'energy_level', 'mood_description', 'recommended_songs']
            if not all(key in mood_data for key in required_keys):
                raise ValueError("Invalid mood analysis format")

            return mood_data

        except json.JSONDecodeError:
            logger.error(f"Failed to parse mood analysis: {content}")
            return {"error": "Couldn't analyze your mood. Try describing it differently."}
        except Exception as e:
            logger.error(f"Mood analysis failed: {e}")
            return {"error": "Mood analysis temporarily unavailable. Please try again."}

    def generate_custom_playlist_ai(self, user_prompt: str, num_songs: int, language: str) -> Dict:
        """Enhanced custom playlist generation with AI song recommendations"""
        if not user_prompt or len(user_prompt.strip()) < 5:
            return {"error": "Please provide a more detailed description of your playlist"}

        try:
            language_context = ""
            if language != "English":
                language_context = f" Focus on {language} music and popular artists from that region."

            prompt = f"""
            Generate a playlist for: '{user_prompt}'
            Language: {language}
            Songs needed: {num_songs}{language_context}

            Return ONLY valid JSON:
            {{
                "playlist_name": "Creative name",
                "description": "Detailed description",
                "genres": ["specific genre1", "specific genre2", "specific genre3"],
                "themes": ["theme1", "theme2"],
                "energy_level": 5,
                "recommended_songs": ["Artist - Song Title", "Artist2 - Song Title2", ...],
                "language_preference": "{language}"
            }}

            IMPORTANT: Recommend exactly {num_songs} real, specific songs with format "Artist - Song Title". Use popular, well-known songs that match the playlist theme and are likely to be on Spotify.
            """

            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1536,
                temperature=0.3
            )

            content = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()

            playlist_data = json.loads(content)
            required_keys = ['playlist_name', 'description', 'genres', 'recommended_songs']
            if not all(key in playlist_data for key in required_keys):
                raise ValueError("Invalid playlist generation format")

            return playlist_data

        except json.JSONDecodeError:
            logger.error(f"Failed to parse playlist generation: {content}")
            return {"error": "Couldn't generate playlist concept. Try rephrasing your request."}
        except Exception as e:
            logger.error(f"Playlist generation failed: {e}")
            return {"error": "Playlist generation temporarily unavailable. Please try again."}

    def search_ai_recommended_tracks(self, search_data: Dict, target_count: int = 20) -> List[str]:
        """Search for AI-recommended specific songs with quality filtering"""
        client = self.get_authenticated_client()
        if not client:
            return []

        track_uris = []
        recommended_songs = search_data.get('recommended_songs', [])
        language = search_data.get('language_preference', 'English')

        # Language-specific markets and popularity thresholds
        language_config = {
            'English': {'markets': ['US', 'GB', 'CA', 'AU'], 'min_popularity': 60},
            'Spanish': {'markets': ['ES', 'MX', 'AR', 'CO'], 'min_popularity': 45},
            'Turkish': {'markets': ['TR'], 'min_popularity': 45},
            'French': {'markets': ['FR', 'CA', 'BE'], 'min_popularity': 45},
            'German': {'markets': ['DE', 'AT', 'CH'], 'min_popularity': 45},
            'Italian': {'markets': ['IT'], 'min_popularity': 45},
            'Portuguese': {'markets': ['BR', 'PT'], 'min_popularity': 45},
            'Japanese': {'markets': ['JP'], 'min_popularity': 40},
            'Korean': {'markets': ['KR'], 'min_popularity': 40}
        }

        config = language_config.get(language, language_config['English'])
        markets = config['markets']
        min_popularity = config['min_popularity']

        logger.info(f"Searching for {len(recommended_songs)} AI-recommended songs with min popularity {min_popularity}")

        try:
            for song_recommendation in recommended_songs:
                if len(track_uris) >= target_count:
                    break

                # Parse "Artist - Song Title" format
                if ' - ' in song_recommendation:
                    artist, title = song_recommendation.split(' - ', 1)
                    artist = artist.strip()
                    title = title.strip()
                else:
                    artist = ""
                    title = song_recommendation.strip()

                # Try different search strategies for each song
                search_queries = []
                if artist and title:
                    search_queries = [
                        f'artist:"{artist}" track:"{title}"',
                        f'"{artist}" "{title}"',
                        f'{artist} {title}',
                        f'track:"{title}"'
                    ]
                else:
                    search_queries = [f'"{title}"', title]

                found_track = False
                for market in markets:
                    if found_track:
                        break

                    for query in search_queries:
                        if found_track:
                            break

                        try:
                            results = client.search(
                                q=query,
                                type='track',
                                limit=10,
                                market=market
                            )

                            for track in results['tracks']['items']:
                                if (track['uri'] not in track_uris and 
                                    track.get('popularity', 0) >= min_popularity and
                                    len(track['artists']) > 0):
                                    
                                    # Additional artist popularity check for quality
                                    try:
                                        artist_info = client.artist(track['artists'][0]['id'])
                                        if artist_info.get('popularity', 0) >= (min_popularity - 20):
                                            track_uris.append(track['uri'])
                                            found_track = True
                                            logger.info(f"Found: {track['artists'][0]['name']} - {track['name']} (Pop: {track.get('popularity', 0)})")
                                            break
                                    except:
                                        # If artist check fails, still add the track if it meets basic criteria
                                        track_uris.append(track['uri'])
                                        found_track = True
                                        logger.info(f"Found: {track['artists'][0]['name']} - {track['name']} (Pop: {track.get('popularity', 0)})")
                                        break

                        except Exception as e:
                            logger.warning(f"Search failed for '{query}' in {market}: {e}")
                            continue

                if not found_track:
                    logger.warning(f"Could not find: {song_recommendation}")

            logger.info(f"Successfully found {len(track_uris)} out of {len(recommended_songs)} AI-recommended tracks")
            return track_uris

        except Exception as e:
            logger.error(f"AI track search failed: {e}")
            return []

    def create_playlist(self, playlist_data: Dict, track_uris: List[str]) -> Dict:
        """Create and populate Spotify playlist"""
        try:
            client = self.get_authenticated_client()
            if not client:
                return {"error": "Authentication required", "auth_needed": True}

            user_info = client.current_user()
            user_id = user_info['id']

            playlist = client.user_playlist_create(
                user=user_id,
                name=playlist_data['name'],
                public=False,
                description=playlist_data['description']
            )

            if not track_uris:
                return {"error": "No tracks found matching your preferences"}

            client.playlist_add_items(playlist['id'], track_uris)

            track_details = []
            if track_uris:
                tracks_info = client.tracks(track_uris[:5])
                for track in tracks_info['tracks']:
                    artist_names = ', '.join([artist['name'] for artist in track['artists']])
                    track_details.append(f"{track['name']} by {artist_names}")

            return {
                "success": True,
                "playlist_url": playlist['external_urls']['spotify'],
                "playlist_name": playlist['name'],
                "track_count": len(track_uris),
                "sample_tracks": track_details
            }

        except Exception as e:
            logger.error(f"Playlist creation failed: {e}")
            return {"error": f"Failed to create playlist: {str(e)}"}

# Initialize Elena DJ
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.info("python-dotenv not available, using system environment")

elena_dj = ElenaDJ()

# API Routes
@app.route('/')
def serve():
    try:
        if os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return '''
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>Elena DJ - Backend Running</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #000; color: #fff; padding: 2rem; text-align: center; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status { background: #1a1a1a; padding: 2rem; border-radius: 8px; margin: 1rem 0; }
                    .success { color: #10b981; }
                    .warning { color: #f59e0b; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎵 Elena DJ Backend Çalışıyor!</h1>
                    <div class="status">
                        <p class="success">✅ Backend API başarıyla çalışıyor (Port 5000)</p>
                        <p class="warning">⚠️ Frontend build bulunamadı</p>
                        <p>Çözüm için şu adımları takip edin:</p>
                        <ol style="text-align: left; display: inline-block;">
                            <li><code>npm install</code> komutunu çalıştırın</li>
                            <li><code>npm run build</code> ile React uygulamasını build edin</li>
                            <li>Sayfayı yenileyin</li>
                        </ol>
                    </div>
                    <p>API Endpoints: <a href="/api/auth-url" style="color: #10b981;">/api/auth-url</a></p>
                </div>
            </body>
            </html>
            ''', 200
    except Exception as e:
        return f"<h1>Elena DJ Backend Error</h1><p>Error: {str(e)}</p>", 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    except Exception:
        return serve()

@app.route('/api/auth-url')
def get_auth_url():
    try:
        auth_url = elena_dj.get_auth_url()
        return jsonify({"auth_url": auth_url, "redirect_uri": elena_dj.redirect_uri})
    except Exception as e:
        logger.error(f"Error getting auth URL: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/spotify-callback')
def spotify_callback():
    """Handle Spotify OAuth callback"""
    try:
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            return f"<h1>Authentication Failed</h1><p>Error: {error}</p><p>Please close this window and try again.</p>"
        
        if code:
            # Construct callback URL for processing
            callback_url = request.url
            success, message = elena_dj.authenticate_with_code(callback_url)
            
            if success:
                return f'''
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Authentication Successful!</h1>
                    <p>{message}</p>
                    <p>You can now close this window and return to Elena DJ.</p>
                    <script>
                        setTimeout(function() {{
                            window.close();
                        }}, 3000);
                    </script>
                </body>
                </html>
                '''
            else:
                return f'''
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ Authentication Failed</h1>
                    <p>{message}</p>
                    <p>Please close this window and try again.</p>
                </body>
                </html>
                '''
        else:
            return "<h1>No authorization code received</h1><p>Please try again.</p>"
            
    except Exception as e:
        logger.error(f"Callback error: {e}")
        return f"<h1>Error</h1><p>{str(e)}</p>"

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    try:
        data = request.get_json()
        callback_url = data.get('callback_url')
        
        if not callback_url:
            return jsonify({"error": "Callback URL is required"}), 400
        
        success, message = elena_dj.authenticate_with_code(callback_url)
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth-status')
def auth_status():
    try:
        is_auth = elena_dj.is_authenticated()
        return jsonify({"authenticated": is_auth})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mood-playlist', methods=['POST'])
def create_mood_playlist():
    try:
        data = request.get_json()
        mood_text = data.get('mood_text', '')
        language = data.get('language', 'English')
        
        if not mood_text:
            return jsonify({"error": "Please describe how you're feeling today!"}), 400

        if not elena_dj.is_authenticated():
            return jsonify({"error": "Authentication required", "auth_needed": True}), 401

        mood_analysis = elena_dj.analyze_mood(mood_text, language)
        if "error" in mood_analysis:
            return jsonify({"error": mood_analysis['error']}), 400

        track_uris = elena_dj.search_ai_recommended_tracks(mood_analysis, 25)
        if not track_uris:
            return jsonify({"error": "Couldn't find quality tracks matching your mood. Try different words."}), 404

        emotion = mood_analysis.get('emotion', 'Mixed').title()
        current_date = datetime.now().strftime('%B %Y')
        playlist_name = f"{emotion} Vibes – {current_date}"

        playlist_data = {
            'name': playlist_name,
            'description': f"🎵 {mood_analysis.get('mood_description', 'Personalized playlist')} | Curated by Elena - Your DJ with {language} preference"
        }

        playlist_result = elena_dj.create_playlist(playlist_data, track_uris)

        if "error" in playlist_result:
            if playlist_result.get("auth_needed"):
                return jsonify({"error": "Authentication expired", "auth_needed": True}), 401
            else:
                return jsonify({"error": playlist_result['error']}), 500

        return jsonify({
            "success": True,
            "playlist": playlist_result,
            "mood_analysis": mood_analysis
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/custom-playlist', methods=['POST'])
def create_custom_playlist():
    try:
        data = request.get_json()
        user_prompt = data.get('user_prompt', '')
        num_songs = data.get('num_songs', 25)
        language = data.get('language', 'English')
        
        if not user_prompt or len(user_prompt.strip()) < 5:
            return jsonify({"error": "Please provide a detailed description of your desired playlist!"}), 400

        if not elena_dj.is_authenticated():
            return jsonify({"error": "Authentication required", "auth_needed": True}), 401

        # Handle auto-detect language
        if language == "Auto-detect":
            language = "English"

        playlist_concept = elena_dj.generate_custom_playlist_ai(user_prompt, num_songs, language)
        if "error" in playlist_concept:
            return jsonify({"error": playlist_concept['error']}), 400

        track_uris = elena_dj.search_ai_recommended_tracks(playlist_concept, num_songs)
        if not track_uris:
            return jsonify({"error": "Couldn't find quality tracks matching your description. Try a different approach."}), 404

        playlist_data = {
            'name': playlist_concept['playlist_name'],
            'description': f"{playlist_concept['description']} | Curated by Elena - Your DJ"
        }

        playlist_result = elena_dj.create_playlist(playlist_data, track_uris)

        if "error" in playlist_result:
            if playlist_result.get("auth_needed"):
                return jsonify({"error": "Authentication expired", "auth_needed": True}), 401
            else:
                return jsonify({"error": playlist_result['error']}), 500

        return jsonify({
            "success": True,
            "playlist": playlist_result,
            "playlist_concept": playlist_concept
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)