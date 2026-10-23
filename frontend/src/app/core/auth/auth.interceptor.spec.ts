import { TestBed } from '@angular/core/testing';
import {
  HttpClient,
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';

import {
  FakeFirebaseAuthGateway,
  fakeFirebaseProvider,
} from '../../../testing/fake-firebase-auth.gateway';
import { authInterceptor } from './auth.interceptor';
import { SessaoStore } from './sessao.store';

describe('authInterceptor', () => {
  let http: HttpClient;
  let controle: HttpTestingController;
  let fake: FakeFirebaseAuthGateway;
  let store: SessaoStore;
  let router: Router;

  beforeEach(() => {
    fake = new FakeFirebaseAuthGateway();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        provideRouter([]),
        fakeFirebaseProvider(fake),
      ],
    });
    http = TestBed.inject(HttpClient);
    controle = TestBed.inject(HttpTestingController);
    store = TestBed.inject(SessaoStore);
    router = TestBed.inject(Router);
    store.limpar();
    store.definirAutenticado(false);
  });

  afterEach(() => controle.verify());

  it('deve enviar o ID Token no Authorization', async () => {
    http.get('http://localhost:8000/api/partidas/atual').subscribe();
    await new Promise((resolve) => setTimeout(resolve));

    const req = controle.expectOne('http://localhost:8000/api/partidas/atual');
    expect(req.request.headers.get('Authorization')).toBe('Bearer id-token');
    req.flush({ partida: null });
  });

  it('não deve interceptar chamadas externas', () => {
    http.get('https://securetoken.google.com/projeto').subscribe();
    const req = controle.expectOne('https://securetoken.google.com/projeto');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('deve deslogar no 401', async () => {
    store.definirSessao({ id: 1, nome: 'Ana', usuario: 'ana' }, 'aluno');
    store.definirAutenticado(true);
    const navegar = spyOn(router, 'navigate').and.resolveTo(true);

    http.get('http://localhost:8000/api/partidas/atual').subscribe({
      error: () => undefined,
    });
    await new Promise((resolve) => setTimeout(resolve));

    const req = controle.expectOne('http://localhost:8000/api/partidas/atual');
    req.flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(fake.sair).toHaveBeenCalled();
    expect(store.autenticado()).toBeFalse();
    expect(navegar).toHaveBeenCalledWith(['/login']);
  });
});
