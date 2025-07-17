
#!/usr/bin/env python3
"""
Elena - Your DJ - AI-Powered Spotify Playlist Generator
A sophisticated music companion that transforms your emotions and ideas into perfect playlists
"""

import json
import os
import re
import hashlib
import gradio as gr
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from groq import Groq
from datetime import datetime
import logging
import sys
import urllib.parse
from typing import Dict, List, Optional, Tuple
import random

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


class ElenaDJ:
    def __init__(self):
        """Initialize Elena - Your DJ with optimized configuration"""
        self.groq_client = None
        self.spotify_clients = {}
        self.spotify_auths = {}
        self.redirect_uri = None
        self.setup_apis()

    def setup_apis(self):
        """Setup APIs with environment support"""
        try:
            # Get API keys
            groq_api_key = os.getenv('GROQ_API_KEY')
            self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
            self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

            if not groq_api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            if not self.spotify_client_id or not self.spotify_client_secret:
                raise ValueError("Spotify credentials not found in environment")

            # Initialize Groq client
            self.groq_client = Groq(api_key=groq_api_key)

            # Setup Spotify OAuth
            self.redirect_uri = self.get_redirect_uri()
            logger.info(f"Using redirect URI: {self.redirect_uri}")

            logger.info("Elena - Your DJ APIs initialized successfully")

        except Exception as e:
            logger.error(f"API setup failed: {e}")
            raise

    def get_redirect_uri(self):
        """Get the correct redirect URI for current environment"""
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
        if redirect_uri:
            return redirect_uri

        replit_domain = os.getenv('REPLIT_DEV_DOMAIN')
        if replit_domain:
            return f"https://{replit_domain}/spotify-callback"

        repl_url = os.getenv('REPL_URL')
        if repl_url:
            if not repl_url.startswith('https://'):
                repl_url = repl_url.replace('http://', 'https://')
            return f"{repl_url}/spotify-callback"

        repl_slug = os.getenv('REPL_SLUG')
        repl_owner = os.getenv('REPL_OWNER')
        if repl_slug and repl_owner:
            return f"https://{repl_slug}.{repl_owner}.repl.co/spotify-callback"

        return "http://127.0.0.1:8080/spotify-callback"

    def create_spotify_auth(self, session_id: str = "default") -> SpotifyOAuth:
        """Create Spotify OAuth object"""
        cache_dir = os.path.join(os.getcwd(), '.cache-spotify')

        try:
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f'spotify_token_{session_id}')
        except Exception as e:
            logger.warning(f"Could not set up cache directory: {e}")
            cache_path = None

        return SpotifyOAuth(
            client_id=self.spotify_client_id,
            client_secret=self.spotify_client_secret,
            redirect_uri=self.redirect_uri,
            scope='playlist-modify-public playlist-modify-private',
            cache_path=cache_path,
            show_dialog=True,
            open_browser=False
        )

    def get_auth_url(self, session_id: str = "default") -> str:
        """Get authorization URL"""
        if session_id not in self.spotify_auths:
            self.spotify_auths[session_id] = self.create_spotify_auth(session_id)
        return self.spotify_auths[session_id].get_authorize_url()

    def authenticate_with_code(self, callback_url: str, session_id: str = "default") -> Tuple[bool, str]:
        """Authenticate using callback URL"""
        try:
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

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False, f"Authentication error: {str(e)}"

    def get_authenticated_client(self, session_id: str = "default") -> Optional[spotipy.Spotify]:
        """Get authenticated Spotify client"""
        for user_id, client in self.spotify_clients.items():
            try:
                client.current_user()
                return client
            except Exception:
                del self.spotify_clients[user_id]
                break

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

            Example:
            {{"emotion": "melancholic", "themes": ["nostalgia", "introspective"], "genres": ["indie folk", "acoustic pop", "singer-songwriter", "alternative rock"], "energy_level": 4, "mood_description": "Reflective and nostalgic", "language_preference": "English", "recommended_songs": ["Bon Iver - Skinny Love", "Iron & Wine - Boy with a Coin", "The National - I Need My Girl", "Phoebe Bridgers - Motion Sickness", "Fleet Foxes - White Winter Hymnal"]}}
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

    def process_mood_request(self, mood_text: str, language: str) -> str:
        """Process mood-based playlist generation with enhanced language support"""
        if not mood_text:
            return "❌ Please describe how you're feeling today!"

        if not self.is_authenticated():
            auth_url = self.get_auth_url()
            return f"""
🔐 **Spotify Authentication Required**

1. **[🎵 Click here to authenticate with Spotify]({auth_url})**
2. Copy the callback URL and paste it in the Authentication section
3. Try generating your playlist again!

**⚠️ Important:** Add this redirect URI to your Spotify app: `{self.redirect_uri}`
            """

        mood_analysis = self.analyze_mood(mood_text, language)
        if "error" in mood_analysis:
            return f"❌ {mood_analysis['error']}"

        track_uris = self.search_ai_recommended_tracks(mood_analysis, 25)
        if not track_uris:
            return "❌ Couldn't find quality tracks matching your mood. Try different words."

        emotion = mood_analysis.get('emotion', 'Mixed').title()
        current_date = datetime.now().strftime('%B %Y')
        playlist_name = f"{emotion} Vibes – {current_date}"

        playlist_data = {
            'name': playlist_name,
            'description': f"🎵 {mood_analysis.get('mood_description', 'Personalized playlist')} | Curated by Elena - Your DJ with {language} preference"
        }

        playlist_result = self.create_playlist(playlist_data, track_uris)

        if "error" in playlist_result:
            if playlist_result.get("auth_needed"):
                auth_url = self.get_auth_url()
                return f"🔐 **Authentication expired. Please [re-authenticate]({auth_url})**"
            else:
                return f"❌ {playlist_result['error']}"

        return f"""
🎧 **{playlist_result['playlist_name']}** is ready!

🔮 **Your Mood:** {mood_analysis['mood_description']}
🌍 **Language:** {language}

📊 **Playlist Details:**
• {playlist_result['track_count']} carefully selected tracks
• Genres: {', '.join(mood_analysis['genres'])}
• Energy Level: {mood_analysis['energy_level']}/10

🎵 **Sample Tracks:**
{chr(10).join([f"• {track}" for track in playlist_result['sample_tracks']])}

🎶 **[🎧 Open in Spotify]({playlist_result['playlist_url']})**
        """

    def process_custom_request(self, user_prompt: str, num_songs: int, language: str) -> str:
        """Process AI-supported custom playlist generation with optimized search"""
        if not user_prompt or len(user_prompt.strip()) < 5:
            return "❌ Please provide a detailed description of your desired playlist!"

        if not self.is_authenticated():
            auth_url = self.get_auth_url()
            return f"""
🔐 **Spotify Authentication Required**

1. **[🎵 Click here to authenticate with Spotify]({auth_url})**
2. Copy the callback URL and paste it in the Authentication section
3. Try creating your playlist again!
            """

        playlist_concept = self.generate_custom_playlist_ai(user_prompt, num_songs, language)
        if "error" in playlist_concept:
            return f"❌ {playlist_concept['error']}"

        track_uris = self.search_ai_recommended_tracks(playlist_concept, num_songs)
        if not track_uris:
            return "❌ Couldn't find quality tracks matching your description. Try a different approach."

        playlist_data = {
            'name': playlist_concept['playlist_name'],
            'description': f"{playlist_concept['description']} | Curated by Elena - Your DJ"
        }

        playlist_result = self.create_playlist(playlist_data, track_uris)

        if "error" in playlist_result:
            if playlist_result.get("auth_needed"):
                auth_url = self.get_auth_url()
                return f"🔐 **Authentication expired. Please [re-authenticate]({auth_url})**"
            else:
                return f"❌ {playlist_result['error']}"

        return f"""
🎧 **{playlist_result['playlist_name']}** is ready!

🤖 **AI Generated Concept:** {playlist_concept['description']}
🌍 **Language:** {language}

📊 **Playlist Details:**
• {playlist_result['track_count']} tracks
• Genres: {', '.join(playlist_concept['genres'])}
• Themes: {', '.join(playlist_concept.get('themes', []))}

🎵 **Sample Tracks:**
{chr(10).join([f"• {track}" for track in playlist_result['sample_tracks']])}

🎶 **[🎧 Open in Spotify]({playlist_result['playlist_url']})**
        """

    def handle_authentication(self, callback_url: str) -> str:
        """Handle authentication callback"""
        if not callback_url or not callback_url.strip():
            return "❌ Please paste the callback URL from Spotify"

        success, message = self.authenticate_with_code(callback_url)

        if success:
            return f"✅ {message}\n\nYou can now generate playlists! Try describing your mood or creating a custom playlist."
        else:
            return f"❌ {message}\n\nPlease try the authentication process again."


def create_gradio_interface():
    """Create the Elena - Your DJ interface with green and black theme"""

    try:
        elena_dj = ElenaDJ()
        logger.info("Elena - Your DJ initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Elena - Your DJ: {e}")
        setup_error = str(e)

        class MockElenaDJ:
            def __init__(self):
                self.redirect_uri = "http://127.0.0.1:8080/spotify-callback"

            def process_mood_request(self, text, language):
                return f"❌ **Setup Error:** {setup_error}"

            def process_custom_request(self, prompt, num_songs, language):
                return f"❌ **Setup Error:** {setup_error}"

            def handle_authentication(self, callback_url):
                return f"❌ **Setup Error:** {setup_error}"

            def get_auth_url(self):
                return "https://accounts.spotify.com/authorize"

        elena_dj = MockElenaDJ()

    # Enhanced language options
    language_options = [
        "English", "Spanish", "French", "German", "Italian", 
        "Portuguese", "Turkish", "Japanese", "Korean", "Arabic", "Hindi"
    ]

    with gr.Blocks(
        title="Elena - Your DJ",
        theme=gr.themes.Base(),
        css="""
        /* Global Variables */
        :root {
            --primary-green: #00ff88;
            --dark-green: #00cc66;
            --light-green: #66ffaa;
            --primary-black: #0a0a0a;
            --secondary-black: #1a1a1a;
            --tertiary-black: #2a2a2a;
            --accent-green: #22ff88;
            --text-white: #ffffff;
            --text-light: #e0e0e0;
            --text-green: #00ff88;
            --border-green: #00ff88;
            --shadow-green: rgba(0, 255, 136, 0.3);
            --gradient-main: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%);
            --gradient-accent: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
            --gradient-card: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
        }
        
        /* Main Container */
        .gradio-container {
            max-width: 1400px !important;
            margin: 0 auto !important;
            font-family: 'SF Pro Display', 'Segoe UI', 'Roboto', sans-serif !important;
            background: var(--gradient-main) !important;
            min-height: 100vh !important;
            color: var(--text-white) !important;
        }
        
        /* Main Header */
        .main-header {
            text-align: center;
            padding: 50px 30px;
            background: var(--gradient-card);
            border: 2px solid var(--border-green);
            border-radius: 25px;
            margin: 30px 0;
            box-shadow: 0 25px 50px var(--shadow-green);
            position: relative;
            overflow: hidden;
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="music-pattern" x="0" y="0" width="25" height="25" patternUnits="userSpaceOnUse"><circle cx="5" cy="20" r="2" fill="rgba(0,255,136,0.1)"/><rect x="7" y="8" width="2" height="12" fill="rgba(0,255,136,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23music-pattern)"/></svg>') repeat;
            opacity: 0.3;
        }
        
        .main-header h1 {
            margin: 0 0 20px 0 !important;
            font-size: 4em !important;
            font-weight: 900 !important;
            background: var(--gradient-accent) !important;
            background-clip: text !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: 0 0 30px var(--shadow-green) !important;
            position: relative;
            z-index: 2;
        }
        
        .main-header h3 {
            margin: 15px 0 !important;
            font-weight: 400 !important;
            font-size: 1.4em !important;
            color: var(--text-light) !important;
            position: relative;
            z-index: 2;
        }
        
        .subtitle {
            font-size: 1.2em !important;
            color: var(--text-green) !important;
            margin-top: 15px !important;
            position: relative;
            z-index: 2;
            font-weight: 500 !important;
        }
        
        /* Setup Instructions */
        .setup-warning {
            background: var(--gradient-card) !important;
            border: 2px solid var(--accent-green) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            margin: 25px 0 !important;
            box-shadow: 0 15px 35px rgba(0, 255, 136, 0.2) !important;
        }
        
        .setup-warning h2, .setup-warning h3, .setup-warning p {
            color: var(--text-light) !important;
        }
        
        .setup-warning strong {
            color: var(--text-green) !important;
        }
        
        /* Authentication Section */
        .auth-section {
            border: 3px solid var(--border-green) !important;
            border-radius: 25px !important;
            padding: 35px !important;
            margin: 35px 0 !important;
            background: var(--gradient-card) !important;
            box-shadow: 0 20px 40px var(--shadow-green) !important;
            position: relative;
        }
        
        .auth-section::before {
            content: '🔐';
            position: absolute;
            top: -20px;
            left: 35px;
            background: var(--gradient-accent);
            color: var(--primary-black);
            padding: 15px 20px;
            border-radius: 50%;
            font-size: 1.8em;
            box-shadow: 0 10px 20px var(--shadow-green);
        }
        
        /* Mode Sections */
        .mode-section {
            border-radius: 25px !important;
            padding: 35px !important;
            margin: 25px 0 !important;
            background: var(--gradient-card) !important;
            border: 2px solid var(--tertiary-black) !important;
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.5) !important;
            transition: all 0.4s ease !important;
        }
        
        .mode-section:hover {
            transform: translateY(-8px) !important;
            box-shadow: 0 25px 50px var(--shadow-green) !important;
            border-color: var(--border-green) !important;
        }
        
        /* Buttons */
        .elena-btn {
            background: var(--gradient-accent) !important;
            color: var(--primary-black) !important;
            border: none !important;
            padding: 20px 40px !important;
            font-size: 18px !important;
            font-weight: 800 !important;
            border-radius: 15px !important;
            box-shadow: 0 10px 25px var(--shadow-green) !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        .elena-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .elena-btn:hover::before {
            left: 100%;
        }
        
        .elena-btn:hover {
            transform: translateY(-4px) scale(1.05) !important;
            box-shadow: 0 15px 35px var(--shadow-green) !important;
        }
        
        /* Output Sections */
        .output-section {
            border-radius: 20px !important;
            padding: 30px !important;
            background: var(--gradient-card) !important;
            margin-top: 30px !important;
            border: 2px solid var(--tertiary-black) !important;
            min-height: 120px !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
            color: var(--text-white) !important;
        }
        
        /* Tab Navigation */
        .tab-nav button {
            font-size: 18px !important;
            font-weight: 700 !important;
            padding: 18px 35px !important;
            border-radius: 15px 15px 0 0 !important;
            transition: all 0.3s ease !important;
            background: var(--secondary-black) !important;
            color: var(--text-light) !important;
            border: 2px solid var(--tertiary-black) !important;
            border-bottom: none !important;
        }
        
        .tab-nav button[aria-selected="true"] {
            background: var(--gradient-accent) !important;
            color: var(--primary-black) !important;
            border-color: var(--border-green) !important;
            box-shadow: 0 -5px 15px var(--shadow-green) !important;
        }
        
        /* Section Titles */
        .section-title {
            color: var(--text-green) !important;
            font-weight: 800 !important;
            margin-bottom: 25px !important;
            font-size: 1.6em !important;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        /* Examples Section */
        .examples-section {
            background: var(--secondary-black) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            margin-top: 30px !important;
            border: 2px solid var(--accent-green) !important;
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.15) !important;
        }
        
        .examples-section h3 {
            color: var(--text-green) !important;
        }
        
        /* Info Section */
        .info-section {
            background: var(--gradient-card) !important;
            border-radius: 20px !important;
            padding: 30px !important;
            margin: 30px 0 !important;
            border-left: 6px solid var(--border-green) !important;
            box-shadow: 0 15px 30px rgba(0, 255, 136, 0.2) !important;
        }
        
        .info-section h2 {
            color: var(--text-green) !important;
        }
        
        .info-section p, .info-section li {
            color: var(--text-light) !important;
        }
        
        /* Creator Credit */
        .creator-credit {
            text-align: center !important;
            margin-top: 50px !important;
            padding: 25px !important;
            background: var(--gradient-accent) !important;
            color: var(--primary-black) !important;
            border-radius: 20px !important;
            font-weight: 700 !important;
            font-size: 1.2em !important;
            box-shadow: 0 15px 30px var(--shadow-green) !important;
        }
        
        /* Form Inputs */
        .input-enhanced {
            border-radius: 15px !important;
            border: 2px solid var(--tertiary-black) !important;
            padding: 18px !important;
            font-size: 16px !important;
            transition: all 0.3s ease !important;
            background: var(--secondary-black) !important;
            color: var(--text-white) !important;
        }
        
        .input-enhanced:focus {
            border-color: var(--border-green) !important;
            box-shadow: 0 0 0 3px var(--shadow-green) !important;
            background: var(--primary-black) !important;
        }
        
        /* Dropdown and Slider */
        .gr-dropdown, .gr-slider {
            background: var(--secondary-black) !important;
            border: 2px solid var(--tertiary-black) !important;
            border-radius: 15px !important;
            color: var(--text-white) !important;
        }
        
        .gr-dropdown:focus-within, .gr-slider:focus-within {
            border-color: var(--border-green) !important;
            box-shadow: 0 0 0 3px var(--shadow-green) !important;
        }
        
        /* Labels */
        label {
            color: var(--text-light) !important;
            font-weight: 600 !important;
            margin-bottom: 8px !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--primary-black);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--gradient-accent);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--dark-green);
        }
        
        /* Animation for buttons */
        @keyframes glow {
            0%, 100% { box-shadow: 0 10px 25px var(--shadow-green); }
            50% { box-shadow: 0 15px 35px rgba(0, 255, 136, 0.5); }
        }
        
        .elena-btn:hover {
            animation: glow 2s ease-in-out infinite;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 2.5em !important;
            }
            
            .mode-section {
                padding: 25px !important;
            }
            
            .auth-section {
                padding: 25px !important;
            }
        }
        """
    ) as app:

        # Enhanced main header with green theme
        with gr.Row(elem_classes=["main-header"]):
            gr.Markdown("""
            # 🎵 Elena - Your DJ
            ### Transform your emotions and ideas into perfect playlists
            **Your AI-powered music companion that understands your vibe**
            <div class="subtitle">🤖 Powered by advanced AI algorithms • 🌍 Multi-language support • 🎵 Quality-filtered tracks</div>
            """)

        # Setup info with green styling
        with gr.Group(elem_classes=["setup-warning"]):
            gr.Markdown(f"""
            **🔧 Setup Instructions:**
            
            1. **Add to Secrets** (🔒 icon in left sidebar):
               - `GROQ_API_KEY`: Get free at [console.groq.com](https://console.groq.com/)
               - `SPOTIFY_CLIENT_ID` & `SPOTIFY_CLIENT_SECRET`: Get at [developer.spotify.com](https://developer.spotify.com/dashboard)

            2. **Add Redirect URI to Spotify App:** `{elena_dj.redirect_uri}`
            
            3. **Deploy on Replit** for best performance and sharing capabilities
            """)

        # Enhanced authentication section
        with gr.Group(elem_classes=["auth-section"]):
            gr.Markdown("## 🔐 Spotify Authentication", elem_classes=["section-title"])
            gr.Markdown("Connect your Spotify account to start creating personalized playlists")

            with gr.Row():
                auth_url_input = gr.Textbox(
                    label="🔗 Paste callback URL from Spotify:",
                    placeholder=f"{elena_dj.redirect_uri}?code=...",
                    lines=2,
                    scale=3,
                    elem_classes=["input-enhanced"]
                )
                auth_btn = gr.Button("🔑 Connect Spotify", variant="primary", scale=1, elem_classes=["elena-btn"])

            auth_result = gr.Markdown("", visible=True, elem_classes=["output-section"])

        # Enhanced main content with redesigned tabs
        with gr.Tabs():
            # Enhanced Mood Mode Tab
            with gr.TabItem("🎭 Mood-Based Discovery"):
                with gr.Group(elem_classes=["mode-section"]):
                    gr.Markdown("### 🎭 Emotion-Driven Playlists", elem_classes=["section-title"])
                    gr.Markdown("**Let Elena analyze your feelings and curate the perfect soundtrack for your mood**")

                    with gr.Row():
                        with gr.Column(scale=3):
                            mood_input = gr.Textbox(
                                label="🎭 Describe your current mood or feelings:",
                                placeholder="Examples: 'feeling nostalgic and dreamy' • 'energetic and ready to conquer' • 'peaceful Sunday morning vibes'",
                                lines=4,
                                elem_classes=["input-enhanced"]
                            )

                        with gr.Column(scale=1):
                            mood_language = gr.Dropdown(
                                label="🌍 Music Language",
                                choices=language_options,
                                value="English",
                                info="Elena will prioritize this language",
                                elem_classes=["input-enhanced"]
                            )

                    mood_generate_btn = gr.Button(
                        "🎵 Create Mood Playlist",
                        variant="primary",
                        size="lg",
                        elem_classes=["elena-btn"]
                    )

                    mood_output = gr.Markdown("", elem_classes=["output-section"])

                    # Enhanced examples
                    with gr.Group(elem_classes=["examples-section"]):
                        gr.Markdown("### 🎨 Mood Examples:")
                        gr.Examples(
                            examples=[
                                ["I feel nostalgic and dreamy, like watching old movies on a rainy day", "English"],
                                ["Stresli ama pozitif kalmaya çalışıyorum, motivasyona ihtiyacım var", "Turkish"],
                                ["Happy and energetic, ready to dance and celebrate life", "Spanish"],
                                ["Mélancolique et introspectif, comme dans les films français", "French"],
                                ["Confident and motivated, pumped up for my workout session", "English"],
                                ["Peaceful and contemplative, need some zen vibes", "Japanese"],
                                ["Romantic and passionate, thinking about someone special", "Italian"],
                                ["Rebellious and edgy, feeling like breaking some rules", "English"]
                            ],
                            inputs=[mood_input, mood_language],
                            label="Try these mood descriptions:"
                        )

            # Enhanced Custom Mode Tab
            with gr.TabItem("🤖 AI-Powered Custom"):
                with gr.Group(elem_classes=["mode-section"]):
                    gr.Markdown("### 🤖 Custom AI Playlists", elem_classes=["section-title"])
                    gr.Markdown("**Describe any playlist idea and let Elena's AI create the perfect tracklist**")

                    with gr.Row():
                        with gr.Column(scale=3):
                            custom_prompt = gr.Textbox(
                                label="🤖 Describe your playlist concept:",
                                placeholder="Examples: 'Epic songs for a road trip through mountains' • 'Chill lo-fi beats for studying late at night' • 'Workout motivation playlist'",
                                lines=4,
                                elem_classes=["input-enhanced"]
                            )

                        with gr.Column(scale=1):
                            custom_language = gr.Dropdown(
                                label="🌍 Music Language",
                                choices=language_options,
                                value="English",
                                info="Elena will prioritize this language",
                                elem_classes=["input-enhanced"]
                            )

                    custom_songs = gr.Slider(
                        label="🎵 Number of Songs",
                        minimum=10,
                        maximum=50,
                        value=25,
                        step=5,
                        info="More songs = better variety and discovery"
                    )

                    custom_generate_btn = gr.Button(
                        "🎵 Generate AI Playlist",
                        variant="primary",
                        size="lg",
                        elem_classes=["elena-btn"]
                    )

                    custom_output = gr.Markdown("", elem_classes=["output-section"])

                    # Enhanced examples
                    with gr.Group(elem_classes=["examples-section"]):
                        gr.Markdown("### 🎨 Playlist Ideas:")
                        gr.Examples(
                            examples=[
                                ["Cozy coffee shop atmosphere with indie and acoustic vibes", 20, "English"],
                                ["Epic workout motivation with high-energy beats", 30, "English"],
                                ["Romantic dinner background music with smooth jazz and soul", 15, "Spanish"],
                                ["Deep focus music for coding and productivity sessions", 40, "English"],
                                ["Sabah rutini için neşeli ve enerjik Türkçe şarkılar", 25, "Turkish"],
                                ["Relaxing spa and meditation soundscape", 35, "English"],
                                ["90s nostalgia trip with the best hits from that decade", 45, "English"],
                                ["Driving at night through the city with synthwave vibes", 30, "English"]
                            ],
                            inputs=[custom_prompt, custom_songs, custom_language],
                            label="Try these playlist concepts:"
                        )

        # Enhanced features section
        with gr.Group(elem_classes=["info-section"]):
            gr.Markdown("""
            ---
            ## 🌟 Elena - Your DJ Features

            **🆕 v2 Optimizations:**

            **🎯 Enhanced AI Algorithms:** Better mood analysis and playlist generation  
            **🎵 Quality Filtering:** Minimum popularity thresholds (60+ for English, 45+ for others)  
            **👥 Artist Verification:** Checks artist popularity for quality assurance  
            **🌍 Market-Specific Search:** Optimized for each language/region  
            **🗣️ Superior Language Support:** Enhanced search terms and cultural context  
            **🎨 Improved UI:** Modern design with better responsive layout  
            **📝 Smart Descriptions:** AI automatically generates contextual playlist descriptions
            """)

        # Enhanced event handlers
        auth_btn.click(
            fn=elena_dj.handle_authentication,
            inputs=auth_url_input,
            outputs=auth_result,
            show_progress=True
        )

        mood_generate_btn.click(
            fn=elena_dj.process_mood_request,
            inputs=[mood_input, mood_language],
            outputs=mood_output,
            show_progress=True
        )

        mood_input.submit(
            fn=elena_dj.process_mood_request,
            inputs=[mood_input, mood_language],
            outputs=mood_output,
            show_progress=True
        )

        custom_generate_btn.click(
            fn=elena_dj.process_custom_request,
            inputs=[custom_prompt, custom_songs, custom_language],
            outputs=custom_output,
            show_progress=True
        )

        # Creator credit with green styling
        with gr.Group(elem_classes=["creator-credit"]):
            gr.Markdown("**Created By Han** • Elena - Your DJ © 2024 • Powered by AI & Music")

    return app


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.info("python-dotenv not available, using system environment")

    app = create_gradio_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=8080,
        share=False,
        debug=True,
        show_error=True
    )
