import { firebaseConfig } from './firebase.config';

export const environment = {
  producao: true,
  // API pública publicada no Render. Use HTTPS e mantenha o sufixo /api.
  apiUrl: 'https://human-ai-aua9.onrender.com/api',
  rankingPollMs: 5000,
  rankingLimite: 500,
  firebase: firebaseConfig,
};
