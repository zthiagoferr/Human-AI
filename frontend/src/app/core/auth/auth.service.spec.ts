import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';

import {
  FakeFirebaseAuthGateway,
  fakeFirebaseProvider,
} from '../../../testing/fake-firebase-auth.gateway';
import { AuthService } from './auth.service';
import { SessaoStore } from './sessao.store';

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;
  let store: SessaoStore;
  let fake: FakeFirebaseAuthGateway;
  let router: Router;

  beforeEach(() => {
    sessionStorage.clear();
    fake = new FakeFirebaseAuthGateway();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        fakeFirebaseProvider(fake),
      ],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
    store = TestBed.inject(SessaoStore);
    router = TestBed.inject(Router);
  });

  afterEach(() => http.verify());

  it('deve entrar pelo Firebase e sincronizar /auth/me', async () => {
    let nome: string | undefined;
    service.login({ email: 'maria@example.com', senha: 'Leitura2026' }).subscribe(
      (usuario) => (nome = usuario.nome),
    );
    await new Promise((resolve) => setTimeout(resolve));

    http.expectOne('http://localhost:8000/api/auth/me').flush({
      usuario: { id: 1, nome: 'Maria', usuario: 'maria' },
      papel: 'aluno',
    });

    expect(nome).toBe('Maria');
    expect(fake.entrar).toHaveBeenCalledWith('maria@example.com', 'Leitura2026');
    expect(store.autenticado()).toBeTrue();
    expect(store.usuario()?.nome).toBe('Maria');
  });

  it('deve cadastrar e provisionar via /auth/sessao', async () => {
    fake.criar.and.resolveTo({
      uid: 'uid-novo',
      email: 'ana@example.com',
      nome: 'Ana',
    });

    let nome: string | undefined;
    service
      .registrar({ nome: 'Ana', email: 'ana@example.com', senha: 'Senha1234' })
      .subscribe((usuario) => (nome = usuario.nome));
    await new Promise((resolve) => setTimeout(resolve));

    const req = http.expectOne('http://localhost:8000/api/auth/sessao');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ nome: 'Ana' });
    req.flush({
      usuario: { id: 2, nome: 'Ana', usuario: 'ana' },
      papel: 'aluno',
    });

    expect(nome).toBe('Ana');
    expect(fake.criar).toHaveBeenCalledWith(
      'ana@example.com',
      'Senha1234',
      'Ana',
    );
    expect(store.autenticado()).toBeTrue();
  });

  it('deve restaurar sessão persistida no reload', async () => {
    fake.usuario = { uid: 'uid-1', email: 'ana@example.com', nome: 'Ana' };

    const inicializacao = service.inicializar();
    await new Promise((resolve) => setTimeout(resolve));

    http.expectOne('http://localhost:8000/api/auth/me').flush({
      usuario: { id: 1, nome: 'Ana', usuario: 'ana' },
      papel: 'aluno',
    });
    await inicializacao;

    expect(fake.configurarPersistencia).toHaveBeenCalled();
    expect(store.autenticado()).toBeTrue();
    expect(store.pronto()).toBeTrue();
    expect(store.usuario()?.nome).toBe('Ana');
  });

  it('deve limpar a sessão no logout', async () => {
    store.definirSessao({ id: 1, nome: 'Ana', usuario: 'ana' }, 'aluno');
    store.definirAutenticado(true);
    const navegar = spyOn(router, 'navigate').and.resolveTo(true);

    service.logout();
    await new Promise((resolve) => setTimeout(resolve));

    expect(fake.sair).toHaveBeenCalled();
    expect(store.autenticado()).toBeFalse();
    expect(navegar).toHaveBeenCalledWith(['/login']);
  });

  it('deve solicitar recuperação de senha', () => {
    service.recuperarSenha('ana@example.com').subscribe();
    expect(fake.recuperarSenha).toHaveBeenCalledWith('ana@example.com');
  });

  it('deve vincular conta legada', () => {
    service.vincularLegado('ABCDE-12345').subscribe((usuario) =>
      expect(usuario.id).toBe(9),
    );

    const req = http.expectOne(
      'http://localhost:8000/api/auth/vincular-legado',
    );
    expect(req.request.body).toEqual({ codigo: 'ABCDE-12345' });
    req.flush({
      usuario: { id: 9, nome: 'Ana', usuario: 'ana' },
      papel: 'aluno',
    });

    expect(store.usuario()?.id).toBe(9);
  });
});
