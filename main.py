
#!/usr/bin/env python3
"""
Elena - Your DJ - AI-Powered Spotify Playlist Generator
A sophisticated music companion that transforms your emotions and ideas into perfect playlists
"""

import json
import os
import re
import gradio as gr
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from groq import Groq
from datetime import datetime
import logging
import sys
import urllib.parse
from typing import Dict, List, Optional, Tuple

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
    """Create the modern Elena - Your DJ interface with theme switcher"""

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

    # Language options
    language_options = [
        "English", "Spanish", "French", "German", "Italian", 
        "Portuguese", "Turkish", "Japanese", "Korean", "Arabic", "Hindi"
    ]

    # Create themes
    dark_theme = gr.themes.Base(
        primary_hue="emerald",
        secondary_hue="slate",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter")],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono")],
    ).set(
        body_background_fill="*neutral_950",
        body_background_fill_dark="*neutral_950",
        background_fill_primary="*neutral_900",
        background_fill_primary_dark="*neutral_900",
        background_fill_secondary="*neutral_800", 
        background_fill_secondary_dark="*neutral_800",
        border_color_primary="*primary_600",
        border_color_primary_dark="*primary_600",
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_500",
        button_primary_text_color="*neutral_900",
        button_secondary_background_fill="*neutral_700",
        button_secondary_background_fill_hover="*neutral_600",
        input_background_fill="*neutral_800",
        input_background_fill_focus="*neutral_700",
        input_border_color="*neutral_600",
        input_border_color_focus="*primary_500",
        block_background_fill="*neutral_800",
        block_border_color="*neutral_600",
        panel_background_fill="*neutral_850",
        slider_color="*primary_600",
        checkbox_background_color="*primary_600",
        checkbox_background_color_selected="*primary_500",
    )

    light_theme = gr.themes.Base(
        primary_hue="emerald",
        secondary_hue="gray",
        neutral_hue="gray",
        font=[gr.themes.GoogleFont("Inter")],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono")],
    ).set(
        body_background_fill="*neutral_50",
        background_fill_primary="*neutral_100",
        background_fill_secondary="*neutral_200",
        border_color_primary="*primary_500",
        button_primary_background_fill="*primary_600",
        button_primary_background_fill_hover="*primary_500",
        button_primary_text_color="white",
        button_secondary_background_fill="*neutral_200",
        button_secondary_background_fill_hover="*neutral_300",
        input_background_fill="white",
        input_background_fill_focus="*neutral_50",
        input_border_color="*neutral_300",
        input_border_color_focus="*primary_400",
        block_background_fill="white",
        block_border_color="*neutral_200",
        panel_background_fill="*neutral_50",
        slider_color="*primary_500",
    )

    # Custom CSS for enhanced styling
    custom_css = """
    /* Global styles */
    .gradio-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #065f46 0%, #059669 50%, #10b981 100%);
        border-radius: 1rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
    }
    
    .header-title {
        font-size: 3.5rem !important;
        font-weight: 900 !important;
        margin-bottom: 1rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 1.5rem !important;
        font-weight: 400 !important;
        opacity: 0.9;
        margin-bottom: 0.5rem !important;
    }
    
    .header-description {
        font-size: 1.1rem !important;
        opacity: 0.8;
    }
    
    /* Card styling */
    .card {
        background: var(--block-background-fill);
        border: 2px solid var(--border-color-primary);
        border-radius: 1rem;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.1);
        transition: all 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.2);
        border-color: var(--primary-500);
    }
    
    /* Auth card special styling */
    .auth-card {
        border: 2px solid #10b981;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(16, 185, 129, 0.1) 100%);
    }
    
    /* Button styling */
    .elena-btn {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 1rem 2rem !important;
        border-radius: 0.75rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3) !important;
    }
    
    .elena-btn:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
    }
    
    /* Tab styling */
    .tab-nav {
        border-radius: 1rem 1rem 0 0;
        overflow: hidden;
    }
    
    .tab-nav button {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        padding: 1rem 2rem !important;
        border-radius: 0 !important;
        transition: all 0.3s ease !important;
    }
    
    .tab-nav button[aria-selected="true"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);
    }
    
    /* Input styling */
    .modern-input {
        border-radius: 0.75rem !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        border: 2px solid var(--input-border-color) !important;
    }
    
    .modern-input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }
    
    /* Output styling */
    .output-card {
        background: var(--panel-background-fill);
        border: 1px solid var(--block-border-color);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-top: 1rem;
        min-height: 100px;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    }
    
    /* Theme switch button */
    .theme-switch {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        border-radius: 50% !important;
        width: 60px !important;
        height: 60px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        font-size: 1.5rem !important;
    }
    
    /* Examples styling */
    .examples-container {
        background: var(--background-fill-secondary);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-top: 1rem;
        border: 1px solid var(--border-color-primary);
    }
    
    /* Features grid */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: var(--background-fill-secondary);
        border: 1px solid var(--border-color-primary);
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        border-color: #10b981;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    /* Status indicators */
    .status-success {
        color: #10b981;
        font-weight: 600;
    }
    
    .status-error {
        color: #ef4444;
        font-weight: 600;
    }
    
    .status-warning {
        color: #f59e0b;
        font-weight: 600;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2.5rem !important;
        }
        
        .card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        .features-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
    }
    
    /* Animations */
    @keyframes glow {
        0%, 100% { box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        50% { box-shadow: 0 6px 25px rgba(16, 185, 129, 0.5); }
    }
    
    .elena-btn:hover {
        animation: glow 2s ease-in-out infinite;
    }
    
    /* Dark mode specific adjustments */
    [data-theme="dark"] .header-container {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%);
    }
    
    /* Light mode header adjustment */
    [data-theme="light"] .header-container {
        background: linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%);
        color: white;
    }
    """

    # State for theme switching
    current_theme = gr.State("dark")

    def switch_theme(theme_state):
        new_theme = "light" if theme_state == "dark" else "dark"
        return new_theme, new_theme

    with gr.Blocks(
        title="Elena - Your DJ",
        theme=dark_theme,
        css=custom_css,
        head="""
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        """
    ) as app:

        # Header section
        with gr.Group(elem_classes=["header-container"]):
            gr.HTML("""
            <div>
                <h1 class="header-title">🎵 Elena - Your DJ</h1>
                <p class="header-subtitle">AI-Powered Spotify Playlist Generator</p>
                <p class="header-description">Transform your emotions and ideas into perfect playlists with advanced AI</p>
            </div>
            """)

        # Theme switcher
        theme_btn = gr.Button("🌙", elem_classes=["theme-switch"], scale=0)

        # Quick setup guide
        with gr.Group(elem_classes=["card"]):
            gr.Markdown("""
            ## 🚀 Quick Setup Guide
            
            **Essential API Keys** (Add to Secrets 🔒):
            - `GROQ_API_KEY` - Get free at [console.groq.com](https://console.groq.com/)
            - `SPOTIFY_CLIENT_ID` & `SPOTIFY_CLIENT_SECRET` - Get at [developer.spotify.com](https://developer.spotify.com/dashboard)
            
            **Important:** Add this redirect URI to your Spotify app settings: `{}`
            """.format(elena_dj.redirect_uri))

        # Authentication section
        with gr.Group(elem_classes=["card", "auth-card"]):
            gr.Markdown("### 🔐 Spotify Authentication")
            gr.Markdown("Connect your Spotify account to start creating personalized playlists")
            
            with gr.Row():
                with gr.Column(scale=4):
                    auth_url_input = gr.Textbox(
                        label="🔗 Paste Spotify callback URL here:",
                        placeholder=f"{elena_dj.redirect_uri}?code=...",
                        lines=2,
                        elem_classes=["modern-input"]
                    )
                with gr.Column(scale=1):
                    auth_btn = gr.Button(
                        "🎵 Connect Spotify", 
                        variant="primary", 
                        elem_classes=["elena-btn"]
                    )
            
            auth_result = gr.Markdown("", elem_classes=["output-card"])

        # Main application tabs
        with gr.Tabs(elem_classes=["tab-nav"]):
            
            # Mood-based playlist tab
            with gr.TabItem("🎭 Mood Discovery", elem_id="mood-tab"):
                with gr.Group(elem_classes=["card"]):
                    gr.Markdown("### 🎭 Emotion-Driven Playlists")
                    gr.Markdown("Describe your current feelings and let Elena create the perfect soundtrack")
                    
                    with gr.Row():
                        with gr.Column(scale=3):
                            mood_input = gr.Textbox(
                                label="💭 How are you feeling today?",
                                placeholder="Examples: 'nostalgic and dreamy' • 'energetic and motivated' • 'peaceful Sunday vibes' • 'melancholic but hopeful'",
                                lines=4,
                                elem_classes=["modern-input"]
                            )
                        with gr.Column(scale=1):
                            mood_language = gr.Dropdown(
                                label="🌍 Music Language",
                                choices=language_options,
                                value="English",
                                elem_classes=["modern-input"]
                            )
                    
                    mood_generate_btn = gr.Button(
                        "🎵 Generate Mood Playlist",
                        variant="primary",
                        size="lg",
                        elem_classes=["elena-btn"]
                    )
                    
                    mood_output = gr.Markdown("", elem_classes=["output-card"])
                    
                    # Mood examples
                    with gr.Group(elem_classes=["examples-container"]):
                        gr.Markdown("### 💡 Try These Mood Examples:")
                        gr.Examples(
                            examples=[
                                ["Feeling nostalgic and dreamy, like watching old movies on a rainy day", "English"],
                                ["Energetic and ready to conquer the world, need pump-up music", "English"],
                                ["Stresli ama pozitif kalmaya çalışıyorum, motivasyona ihtiyacım var", "Turkish"],
                                ["Mélancolique et introspectif, besoin de musique douce", "French"],
                                ["Peaceful and contemplative, seeking zen and mindfulness", "English"],
                                ["Romantic and passionate, thinking about someone special", "Spanish"],
                                ["Confident and rebellious, feeling like breaking some rules", "English"],
                                ["Tired but hopeful, end of a long day but optimistic", "English"]
                            ],
                            inputs=[mood_input, mood_language]
                        )

            # Custom playlist tab
            with gr.TabItem("🤖 Custom AI Playlists", elem_id="custom-tab"):
                with gr.Group(elem_classes=["card"]):
                    gr.Markdown("### 🤖 AI-Powered Custom Playlists")
                    gr.Markdown("Describe any playlist concept and let Elena's AI create the perfect tracklist")
                    
                    with gr.Row():
                        with gr.Column(scale=3):
                            custom_prompt = gr.Textbox(
                                label="🎯 Describe your playlist concept:",
                                placeholder="Examples: 'Epic road trip through mountains' • 'Cozy coffee shop atmosphere' • 'Intense workout motivation' • 'Late night coding session'",
                                lines=4,
                                elem_classes=["modern-input"]
                            )
                        with gr.Column(scale=1):
                            custom_language = gr.Dropdown(
                                label="🌍 Music Language",
                                choices=language_options,
                                value="English",
                                elem_classes=["modern-input"]
                            )
                    
                    custom_songs = gr.Slider(
                        label="🎵 Number of Songs",
                        minimum=10,
                        maximum=50,
                        value=25,
                        step=5,
                        elem_classes=["modern-input"]
                    )
                    
                    custom_generate_btn = gr.Button(
                        "🎵 Generate AI Playlist",
                        variant="primary",
                        size="lg",
                        elem_classes=["elena-btn"]
                    )
                    
                    custom_output = gr.Markdown("", elem_classes=["output-card"])
                    
                    # Custom playlist examples
                    with gr.Group(elem_classes=["examples-container"]):
                        gr.Markdown("### 💡 Try These Playlist Concepts:")
                        gr.Examples(
                            examples=[
                                ["Cozy coffee shop atmosphere with indie and acoustic vibes", 20, "English"],
                                ["Epic workout motivation with high-energy electronic beats", 30, "English"],
                                ["Romantic dinner background music with smooth jazz and soul", 15, "English"],
                                ["Deep focus music for coding and productivity sessions", 40, "English"],
                                ["Driving at night through the city with synthwave vibes", 25, "English"],
                                ["Sabah rutini için neşeli ve enerjik Türkçe şarkılar", 25, "Turkish"],
                                ["Relaxing spa and meditation soundscape", 35, "English"],
                                ["90s nostalgia trip with the best hits from that decade", 45, "English"]
                            ],
                            inputs=[custom_prompt, custom_songs, custom_language]
                        )

        # Features showcase
        with gr.Group(elem_classes=["card"]):
            gr.Markdown("## 🌟 Elena DJ Features")
            
            gr.HTML("""
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <h3>Advanced AI Analysis</h3>
                    <p>Powered by LLaMA 3 70B for sophisticated mood understanding and music curation</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <h3>Quality Filtering</h3>
                    <p>Smart popularity thresholds and artist verification ensure high-quality tracks</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🌍</div>
                    <h3>Multi-Language Support</h3>
                    <p>Optimized search algorithms for 11+ languages with regional market targeting</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🔒</div>
                    <h3>Secure Integration</h3>
                    <p>OAuth 2.0 authentication with Spotify for safe and private playlist creation</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <h3>Instant Creation</h3>
                    <p>Generate and populate playlists directly in your Spotify account within seconds</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎨</div>
                    <h3>Smart Descriptions</h3>
                    <p>AI-generated contextual playlist names and descriptions that capture your vibe</p>
                </div>
            </div>
            """)

        # Creator credit
        with gr.Group(elem_classes=["card"]):
            gr.Markdown("""
            ---
            ### 👨‍💻 Created by Han
            **Elena - Your DJ** © 2024 • Built with ❤️ for Elena • Powered by AI & Music
            
            *A sophisticated music companion that transforms emotions into perfect playlists*
            """, elem_classes=["text-center"])

        # Event handlers
        theme_btn.click(
            fn=switch_theme,
            inputs=[current_theme],
            outputs=[current_theme, app],
            show_progress=False
        )

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
