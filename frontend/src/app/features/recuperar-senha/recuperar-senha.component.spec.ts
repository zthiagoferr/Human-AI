import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import {
  FakeFirebaseAuthGateway,
  fakeFirebaseProvider,
} from '../../../testing/fake-firebase-auth.gateway';
import { AuthService } from '../../core/auth/auth.service';
import { RecuperarSenhaComponent } from './recuperar-senha.component';

describe('RecuperarSenhaComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RecuperarSenhaComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        fakeFirebaseProvider(new FakeFirebaseAuthGateway()),
      ],
    }).compileComponents();
  });

  it('deve enviar recuperação e mostrar mensagem genérica', () => {
    const fixture = TestBed.createComponent(RecuperarSenhaComponent);
    const componente = fixture.componentInstance;
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'recuperarSenha').and.returnValue(of(undefined));

    componente.form.setValue({ email: 'ana@example.com' });
    componente.enviar();

    expect(auth.recuperarSenha).toHaveBeenCalledWith('ana@example.com');
    expect(componente.enviado()).toBeTrue();
    expect(componente.erro()).toBeNull();
  });

  it('deve exibir erro de rede em português', () => {
    const fixture = TestBed.createComponent(RecuperarSenhaComponent);
    const componente = fixture.componentInstance;
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'recuperarSenha').and.returnValue(
      throwError(() => ({ code: 'auth/network-request-failed' })),
    );

    componente.form.setValue({ email: 'ana@example.com' });
    componente.enviar();

    expect(componente.erro()).toContain('Não foi possível conectar');
  });
});
