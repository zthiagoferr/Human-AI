import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { SessaoStore } from './sessao.store';

export const guestGuard: CanActivateFn = () => {
  const store = inject(SessaoStore);
  const router = inject(Router);
  return store.autenticado() ? router.createUrlTree(['/jogo']) : true;
};
