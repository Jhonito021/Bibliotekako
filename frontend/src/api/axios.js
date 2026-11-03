// src/api/axios.js
import axios from 'axios';

const api = axios.create({
  // On utilise 127.0.0.1 pour éviter les problèmes de résolution IPv6 (localhost)
  baseURL: 'http://127.0.0.1:5000/api', 
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur de requête : Ajoute le token JWT avant chaque envoi
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercepteur de réponse : Gère l'expiration du token (Erreur 401)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Si le token est invalide ou expiré, on nettoie et on redirige
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      // Optionnel : forcer la redirection vers /login
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;