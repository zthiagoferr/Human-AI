import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { mensagemErroAuth } from '../../core/firebase/firebase-errors';
import { AvisoComponent } from '../../shared/components/aviso/aviso.component';
import { MarcaComponent } from '../../shared/components/marca/marca.component';

@Component({
  selector: 'app-vincular-legado',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, MarcaComponent, AvisoComponent],
  templateUrl: './vincular-legado.component.html',
  styleUrl: './vincular-legado.component.scss',
})
export class VincularLegadoComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly carregando = signal(false);
  readonly concluido = signal(false);
  readonly erro = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    codigo: ['', [Validators.required, Validators.maxLength(40)]],
  });

  enviar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.carregando.set(true);
    this.erro.set(null);
    this.auth.vincularLegado(this.form.getRawValue().codigo).subscribe({
      next: () => {
        this.carregando.set(false);
        this.concluido.set(true);
      },
      error: (erro: unknown) => {
        this.carregando.set(false);
        this.erro.set(mensagemErroAuth(erro));
      },
    });
  }

  irParaJogo(): void {
    void this.router.navigate(['/jogo']);
  }
}
