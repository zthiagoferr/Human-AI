import { FirebaseApp, getApp, getApps, initializeApp } from 'firebase/app';
import { Auth, getAuth } from 'firebase/auth';

import { environment } from '../../../environments/environment';

let autenticacao: Auth | undefined;

export function obterAuth(): Auth {
  if (!environment.firebase.apiKey || !environment.firebase.appId) {
    throw new Error(
      'A configuração pública do Firebase está incompleta. Procure o professor.',
    );
  }
  if (!autenticacao) {
    const app: FirebaseApp = getApps().length
      ? getApp()
      : initializeApp(environment.firebase);
    autenticacao = getAuth(app);
  }
  return autenticacao;
}
