import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { throwError } from 'rxjs';

import {
  FakeFirebaseAuthGateway,
  fakeFirebaseProvider,
} from '../../../testing/fake-firebase-auth.gateway';
import { AuthService } from '../../core/auth/auth.service';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let fake: FakeFirebaseAuthGateway;

  beforeEach(async () => {
    fake = new FakeFirebaseAuthGateway();
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        fakeFirebaseProvider(fake),
      ],
    }).compileComponents();
  });

  it('deve iniciar com formulário inválido', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    expect(fixture.componentInstance.form.invalid).toBeTrue();
  });

  it('deve exibir mensagem em português para senha incorreta', () => {
    const fixture = TestBed.createComponent(LoginComponent);
    const componente = fixture.componentInstance;
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'login').and.returnValue(
      throwError(() => ({ code: 'auth/wrong-password' })),
    );

    componente.form.setValue({
      email: 'ana@example.com',
      senha: 'senha-errada',
    });
    componente.enviar();

    expect(componente.erro()).toBe('E-mail ou senha inválidos.');
    expect(componente.carregando()).toBeFalse();
  });
});
