
import axios from 'axios';

const API_BASE = '/api';

export const getAuthUrl = async () => {
  const response = await axios.get(`${API_BASE}/auth-url`);
  return response.data;
};

export const authenticate = async (callbackUrl) => {
  const response = await axios.post(`${API_BASE}/authenticate`, {
    callback_url: callbackUrl
  });
  return response.data;
};

export const checkAuthStatus = async () => {
  const response = await axios.get(`${API_BASE}/auth-status`);
  return response.data;
};

export const createMoodPlaylist = async (moodText, language) => {
  const response = await axios.post(`${API_BASE}/mood-playlist`, {
    mood_text: moodText,
    language: language
  });
  return response.data;
};

export const createCustomPlaylist = async (userPrompt, numSongs, language) => {
  const response = await axios.post(`${API_BASE}/custom-playlist`, {
    user_prompt: userPrompt,
    num_songs: numSongs,
    language: language
  });
  return response.data;
};
import axios from 'axios';

const API_BASE = '/api';

export const getAuthUrl = async () => {
  const response = await axios.get(`${API_BASE}/auth-url`);
  return response.data;
};

export const authenticate = async (callbackUrl) => {
  const response = await axios.post(`${API_BASE}/authenticate`, {
    callback_url: callbackUrl
  });
  return response.data;
};

export const checkAuthStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE}/auth-status`);
    return response.data.authenticated;
  } catch (error) {
    return false;
  }
};

export const createMoodPlaylist = async (moodText, language) => {
  const response = await axios.post(`${API_BASE}/mood-playlist`, {
    mood_text: moodText,
    language: language
  });
  return response.data;
};

export const createCustomPlaylist = async (userPrompt, numSongs, language) => {
  const response = await axios.post(`${API_BASE}/custom-playlist`, {
    user_prompt: userPrompt,
    num_songs: numSongs,
    language: language
  });
  return response.data;
};
