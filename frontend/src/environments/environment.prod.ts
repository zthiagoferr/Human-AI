import { firebaseConfig } from './firebase.config';

export const environment = {
  producao: true,
  // A API pública ainda não foi publicada. Mantenha vazio para que a interface
  // informe a indisponibilidade e nunca simule partidas, resultados ou ranking.
  // Quando a API existir, troque por uma URL HTTPS, por exemplo:
  // apiUrl: 'https://api.exemplo.org/api',
  apiUrl: '',
  rankingPollMs: 5000,
  rankingLimite: 500,
  firebase: firebaseConfig,
};
