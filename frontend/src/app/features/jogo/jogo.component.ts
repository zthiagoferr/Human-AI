import {
  Component,
  computed,
  DestroyRef,
  ElementRef,
  inject,
  OnInit,
  signal,
  ViewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';
import { Escolha } from '../../core/models/carta.models';
import { Partida } from '../../core/models/partida.models';
import { PartidaService } from '../../core/services/partida.service';
import { RankingService } from '../../core/services/ranking.service';
import { mensagemErro } from '../../core/utils/erro';
import { AvisoComponent } from '../../shared/components/aviso/aviso.component';
import { MarcaComponent } from '../../shared/components/marca/marca.component';
import { CartaComponent } from './carta/carta.component';

type RespostaForm = FormGroup<{
  cartaId: FormControl<string>;
  escolha: FormControl<Escolha | null>;
}>;

@Component({
  selector: 'app-jogo',
  standalone: true,
  imports: [ReactiveFormsModule, MarcaComponent, AvisoComponent, CartaComponent],
  templateUrl: './jogo.component.html',
  styleUrl: './jogo.component.scss',
})
export class JogoComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly partidaService = inject(PartidaService);
  private readonly rankingService = inject(RankingService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  @ViewChild('tituloCarta') private tituloCarta?: ElementRef<HTMLElement>;

  private inscricaoValores?: Subscription;

  readonly total = 22;
  readonly marcos = Array.from({ length: 22 }, (_, indice) => indice);
  readonly partida = this.partidaService.partida;
  readonly carregando = signal(true);
  readonly enviando = signal(false);
  readonly erro = signal<string | null>(null);
  readonly indiceAtual = signal(0);
  readonly progresso = signal(0);
  readonly atualRespondida = signal(false);
  readonly formValido = signal(false);

  readonly form = this.fb.group({
    respostas: this.fb.array<RespostaForm>([]),
  });

  readonly cartaAtual = computed(() => {
    const partida = this.partida();
    return partida?.cartas[this.indiceAtual()] ?? null;
  });

  get respostas(): FormArray<RespostaForm> {
    return this.form.controls.respostas;
  }

  get grupoAtual(): RespostaForm | null {
    return this.respostas.at(this.indiceAtual()) ?? null;
  }

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando.set(true);
    this.erro.set(null);
    this.partidaService.obterOuIniciar().subscribe({
      next: (partida) => {
        this.montarFormulario(partida);
        this.carregando.set(false);
      },
      error: (erro: unknown) => {
        this.erro.set(mensagemErro(erro));
        this.carregando.set(false);
      },
    });
  }

  private montarFormulario(partida: Partida): void {
    const grupos = partida.cartas.map((carta) =>
      this.fb.group({
        cartaId: this.fb.nonNullable.control(carta.id),
        escolha: this.fb.control<Escolha | null>(null, Validators.required),
      }),
    );
    this.form.setControl('respostas', this.fb.array<RespostaForm>(grupos));
    this.indiceAtual.set(0);

    const salvas = this.partidaService.lerRespostas(partida.id);
    for (const grupo of this.respostas.controls) {
      const escolha = salvas[grupo.controls.cartaId.value];
      if (escolha === 'humano' || escolha === 'ia') {
        grupo.controls.escolha.setValue(escolha);
      }
    }

    this.inscricaoValores?.unsubscribe();
    this.inscricaoValores = this.form.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.persistir(partida.id);
        this.atualizarEstado();
      });

    this.atualizarEstado();
  }

  private persistir(partidaId: number): void {
    const valores: Record<string, Escolha | null> = {};
    for (const grupo of this.respostas.controls) {
      valores[grupo.controls.cartaId.value] = grupo.controls.escolha.value;
    }
    this.partidaService.salvarRespostas(partidaId, valores);
  }

  private atualizarEstado(): void {
    const respondidas = this.respostas.controls.filter(
      (grupo) => !!grupo.controls.escolha.value,
    ).length;
    this.progresso.set(respondidas);
    this.formValido.set(respondidas === this.total);
    this.atualRespondida.set(!!this.grupoAtual?.controls.escolha.value);
  }

  anterior(): void {
    if (this.indiceAtual() > 0) {
      this.indiceAtual.update((indice) => indice - 1);
      this.atualizarEstado();
      this.focarTitulo();
    }
  }

  proxima(): void {
    if (!this.atualRespondida() || this.indiceAtual() >= this.total - 1) {
      return;
    }
    this.indiceAtual.update((indice) => indice + 1);
    this.atualizarEstado();
    this.focarTitulo();
  }

  private focarTitulo(): void {
    setTimeout(() => this.tituloCarta?.nativeElement.focus(), 0);
  }

  finalizar(): void {
    if (!this.formValido()) {
      this.form.markAllAsTouched();
      return;
    }
    const partida = this.partida();
    if (!partida) {
      return;
    }
    const respostas = this.respostas.controls.map((grupo) => ({
      cartaId: grupo.controls.cartaId.value,
      escolha: grupo.controls.escolha.value as Escolha,
    }));
    this.enviando.set(true);
    this.erro.set(null);
    this.partidaService.enviarRespostas(partida.id, respostas).subscribe({
      next: (resultado) => {
        this.enviando.set(false);
        this.rankingService.notificarConclusao();
        void this.router.navigate(['/resultado', resultado.partidaId]);
      },
      error: (erro: unknown) => {
        this.enviando.set(false);
        this.erro.set(mensagemErro(erro));
      },
    });
  }

  desistir(): void {
    const partida = this.partida();
    if (!partida) {
      return;
    }
    const confirmado = window.confirm(
      'Desistir abandona esta tentativa e inicia outra partida. Deseja continuar?',
    );
    if (!confirmado) {
      return;
    }
    this.partidaService.abandonar(partida.id).subscribe({
      next: () => {
        this.partidaService.limparEstado();
        this.carregar();
      },
      error: (erro: unknown) => this.erro.set(mensagemErro(erro)),
    });
  }

  sair(): void {
    this.auth.logout();
  }
}
