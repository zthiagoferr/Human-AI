import { Provider } from '@angular/core';

import { FirebaseAuthGateway } from '../app/core/firebase/firebase-auth.gateway';
import { UsuarioFirebase } from '../app/core/firebase/firebase-auth.models';

export class FakeFirebaseAuthGateway {
  usuario: UsuarioFirebase | null = null;
  tokenAtual: string | null = 'id-token';

  configurarPersistencia = jasmine
    .createSpy('configurarPersistencia')
    .and.resolveTo();

  aguardarPronto = jasmine
    .createSpy('aguardarPronto')
    .and.callFake(async () => this.usuario);

  observar = jasmine
    .createSpy('observar')
    .and.callFake((callback: (usuario: UsuarioFirebase | null) => void) => {
      callback(this.usuario);
      return () => undefined;
    });

  entrar = jasmine
    .createSpy('entrar')
    .and.callFake(async (email: string) => {
      this.usuario = {
        uid: 'uid-teste',
        email,
        nome: 'Aluno Teste',
      };
      return this.usuario;
    });

  criar = jasmine
    .createSpy('criar')
    .and.callFake(async (email: string, _senha: string, nome: string) => {
      this.usuario = { uid: 'uid-novo', email, nome };
      return this.usuario;
    });

  sair = jasmine.createSpy('sair').and.callFake(async () => {
    this.usuario = null;
  });

  recuperarSenha = jasmine
    .createSpy('recuperarSenha')
    .and.resolveTo();

  token = jasmine.createSpy('token').and.callFake(async () => this.tokenAtual);

  usuarioAtual = jasmine
    .createSpy('usuarioAtual')
    .and.callFake(() => this.usuario);
}

export function fakeFirebaseProvider(
  fake: FakeFirebaseAuthGateway,
): Provider {
  return { provide: FirebaseAuthGateway, useValue: fake };
}
