import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { mensagemErroAuth } from '../../core/firebase/firebase-errors';
import { AvisoComponent } from '../../shared/components/aviso/aviso.component';
import { MarcaComponent } from '../../shared/components/marca/marca.component';

function senhasIguais(controle: AbstractControl): ValidationErrors | null {
  const senha = controle.get('senha')?.value;
  const confirmar = controle.get('confirmarSenha')?.value;
  return senha === confirmar ? null : { senhasDiferentes: true };
}

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, MarcaComponent, AvisoComponent],
  templateUrl: './registro.component.html',
  styleUrl: './registro.component.scss',
})
export class RegistroComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly carregando = signal(false);
  readonly erro = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group(
    {
      nome: [
        '',
        [
          Validators.required,
          Validators.minLength(3),
          Validators.maxLength(80),
          Validators.pattern(/^[\p{L}][\p{L}\p{M}' .-]*$/u),
        ],
      ],
      email: [
        '',
        [Validators.required, Validators.email, Validators.maxLength(254)],
      ],
      senha: [
        '',
        [
          Validators.required,
          Validators.minLength(8),
          Validators.maxLength(128),
          Validators.pattern(/^(?=.*[A-Za-zÀ-ÿ])(?=.*\d).+$/),
        ],
      ],
      confirmarSenha: ['', [Validators.required]],
    },
    { validators: senhasIguais },
  );

  enviar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.carregando.set(true);
    this.erro.set(null);
    const { nome, email, senha } = this.form.getRawValue();
    this.auth.registrar({ nome, email, senha }).subscribe({
      next: () => {
        this.carregando.set(false);
        void this.router.navigate(['/jogo']);
      },
      error: (erro: unknown) => {
        this.carregando.set(false);
        this.erro.set(mensagemErroAuth(erro));
      },
    });
  }
}
