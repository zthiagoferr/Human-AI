import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import {
  FakeFirebaseAuthGateway,
  fakeFirebaseProvider,
} from '../../../testing/fake-firebase-auth.gateway';
import { RegistroComponent } from './registro.component';

describe('RegistroComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RegistroComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        fakeFirebaseProvider(new FakeFirebaseAuthGateway()),
      ],
    }).compileComponents();
  });

  it('deve validar confirmação de senha', () => {
    const fixture = TestBed.createComponent(RegistroComponent);
    const form = fixture.componentInstance.form;
    form.patchValue({
      nome: 'Aluno Teste',
      email: 'aluno@example.com',
      senha: 'Senha1234',
      confirmarSenha: 'Senha1234',
    });
    expect(form.valid).toBeTrue();
    form.controls.confirmarSenha.setValue('Outra1234');
    expect(form.hasError('senhasDiferentes')).toBeTrue();
  });

  it('deve rejeitar e-mail inválido', () => {
    const fixture = TestBed.createComponent(RegistroComponent);
    const form = fixture.componentInstance.form;
    form.patchValue({
      nome: 'Aluno Teste',
      email: 'invalido',
      senha: 'Senha1234',
      confirmarSenha: 'Senha1234',
    });
    expect(form.controls.email.invalid).toBeTrue();
  });
});
