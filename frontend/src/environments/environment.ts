import { firebaseConfig } from './firebase.config';

export const environment = {
  producao: false,
  apiUrl: 'http://localhost:8000/api',
  rankingPollMs: 5000,
  rankingLimite: 500,
  firebase: firebaseConfig,
};
