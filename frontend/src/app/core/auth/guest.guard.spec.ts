import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
} from '@angular/router';

import { guestGuard } from './guest.guard';
import { SessaoStore } from './sessao.store';

describe('guestGuard', () => {
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
      guestGuard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot),
    );

  it('deve permitir sem sessão', () => {
    expect(executar()).toBeTrue();
  });

  it('deve redirecionar autenticado para o jogo', () => {
    store.definirSessao(
      { id: 1, nome: 'Aluno', usuario: 'aluno' },
      'aluno',
    );
    store.definirAutenticado(true);
    expect(executar()).toEqual(router.createUrlTree(['/jogo']));
  });
});
