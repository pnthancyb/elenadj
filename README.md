# Elena 🎧🤖

**AI-powered Spotify playlist creator based on your emotions & preferences.**

---

## 🚀 Overview

**Elena** is a smart music companion that transforms your feelings, thoughts, and ideas into perfect Spotify playlists. Powered by advanced AI and designed for personal expression, Elena can analyze your mood or turn any playlist concept into a custom tracklist.

Whether you're seeking the perfect soundtrack for a rainy day, an epic workout, or just want to discover music that matches your vibe, Elena is here for you.

---

## 🛠️ Built With

- 🧠 **Groq** (LLaMA 3 via Groq API)
- 🎧 **Spotify Web API**
- 🖼️ **Gradio** (Custom dual-mode UI)

---

## 🎯 Features (Current Version: v2.0)

- **Mood-based playlist generation**: Just describe your feelings, let Elena create the vibe.
- **Custom playlist creation**: Describe any concept, get a ready-to-listen playlist.
- **Spotify OAuth integration**: Secure connection to your account, private playlists.
- **Clean & responsive Gradio interface**: Fresh look, easy controls, modern design.

---

## 🌱 Coming Soon: v3 

Elena will soon:
- Generate album covers via Gemini Flash
- Add Spotify playlist art & image preview
- Improve AI reasoning for even deeper mood matching

Yes, I will build v3.
Because her name is Elena.

❤️ **Endless thanks to Elena**  
I wrote the code, but she gave it heart.

---

## 👨‍💻 About the Creator

Hi! I'm Han, a young developer (just 17 years old!) and this is my first time building a full Gradio interface.  
If you notice any beginner mistakes or rough UI patches, that's because I'm still learning and growing.  
I started this project for fun, and for my wife.  
Hope you enjoy it as much as we do!

---

## ⚡ Quick Start

1. **Clone the repo**

   ```bash
   git clone https://github.com/pnthancyb/elenadj.git
   cd elenadj
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment variables**

   Add your keys to `.env` (create if missing):

   ```
   GROQ_API_KEY=your_groq_api_key
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=your_redirect_uri
   ```

   > You can get Groq API key [here](https://console.groq.com/) and Spotify keys [here](https://developer.spotify.com/dashboard).

4. **Run the app**

   ```bash
   python main.py
   ```

   Visit the Gradio UI at `http://localhost:8080` (or your deployed address).

---

## ✨ Tech Notes

- **AI Model:** Uses Groq's LLaMA 3 (70B) for mood & playlist analysis.
- **Spotify:** Full playlist management via Web API.
- **Gradio:** Modern UI with dual modes — mood and custom playlist.

---

## 💡 Inspiration

Elena is more than just code — it's a gift, an experiment, and a small piece of my heart.  
Thank you, Elena, for being my muse.  
And thanks to anyone who tries this out!

---

## 📫 Contact

Questions, feedback, or just want to say hi?  
Open an [issue](https://github.com/pnthancyb/elenadj/issues) or reach me on GitHub.

---

**Elena - Your DJ © 2024 — Powered by Han & Elena**
