import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
} from '@angular/router';

import { authGuard } from './auth.guard';
import { SessaoStore } from './sessao.store';

describe('authGuard', () => {
  let store: SessaoStore;
  let router: Router;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({ providers: [provideRouter([])] });
    store = TestBed.inject(SessaoStore);
    router = TestBed.inject(Router);
    store.limpar();
    store.definirAutenticado(false);
  });

  const executar = () =>
    TestBed.runInInjectionContext(() =>
      authGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );

  it('deve redirecionar para login sem sessão', () => {
    expect(executar()).toEqual(router.createUrlTree(['/login']));
  });

  it('deve permitir com sessão', () => {
    store.definirSessao(
      { id: 1, nome: 'Aluno', usuario: 'aluno' },
      'aluno',
    );
    store.definirAutenticado(true);
    expect(executar()).toBeTrue();
  });
});
