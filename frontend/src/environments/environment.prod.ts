import { firebaseConfig } from './firebase.config';

export const environment = {
  producao: true,
  // Em produção, altere esta URL para a URL HTTPS real da API antes do build.
  apiUrl: 'http://localhost:8000/api',
  rankingPollMs: 5000,
  rankingLimite: 500,
  firebase: firebaseConfig,
};
