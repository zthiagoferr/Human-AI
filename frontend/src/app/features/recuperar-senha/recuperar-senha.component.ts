import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import {
  ehErroUsuarioNaoEncontrado,
  mensagemErroAuth,
} from '../../core/firebase/firebase-errors';
import { AvisoComponent } from '../../shared/components/aviso/aviso.component';
import { MarcaComponent } from '../../shared/components/marca/marca.component';

@Component({
  selector: 'app-recuperar-senha',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, MarcaComponent, AvisoComponent],
  templateUrl: './recuperar-senha.component.html',
  styleUrl: './recuperar-senha.component.scss',
})
export class RecuperarSenhaComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);

  readonly carregando = signal(false);
  readonly enviado = signal(false);
  readonly erro = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    email: [
      '',
      [Validators.required, Validators.email, Validators.maxLength(254)],
    ],
  });

  enviar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.carregando.set(true);
    this.erro.set(null);
    this.auth.recuperarSenha(this.form.getRawValue().email).subscribe({
      next: () => {
        this.carregando.set(false);
        this.enviado.set(true);
      },
      error: (erro: unknown) => {
        this.carregando.set(false);
        if (ehErroUsuarioNaoEncontrado(erro)) {
          this.enviado.set(true);
          return;
        }
        this.erro.set(mensagemErroAuth(erro));
      },
    });
  }
}
