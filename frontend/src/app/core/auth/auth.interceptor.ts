import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, from, of, switchMap, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FirebaseAuthGateway } from '../firebase/firebase-auth.gateway';
import { SessaoStore } from './sessao.store';

export const authInterceptor: HttpInterceptorFn = (requisicao, proximo) => {
  const gateway = inject(FirebaseAuthGateway);
  const store = inject(SessaoStore);
  const router = inject(Router);

  if (!requisicao.url.startsWith(environment.apiUrl)) {
    return proximo(requisicao);
  }

  return from(gateway.token()).pipe(
    catchError(() => of(null)),
    switchMap((token) => {
      const autorizada = token
        ? requisicao.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
        : requisicao;
      return proximo(autorizada);
    }),
    catchError((erro: unknown) => {
      if (erro instanceof HttpErrorResponse && erro.status === 401) {
        void gateway.sair().catch(() => undefined);
        store.limpar();
        if (!router.url.startsWith('/login')) {
          void router.navigate(['/login']);
        }
      }
      return throwError(() => erro);
    }),
  );
};
