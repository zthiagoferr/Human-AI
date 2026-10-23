import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { ResultadoPartida } from '../../core/models/partida.models';
import { RankingItem } from '../../core/models/ranking.models';
import { PartidaService } from '../../core/services/partida.service';
import { RankingService } from '../../core/services/ranking.service';
import { mensagemErro } from '../../core/utils/erro';
import { AvisoComponent } from '../../shared/components/aviso/aviso.component';
import { MarcaComponent } from '../../shared/components/marca/marca.component';
import { DuracaoPipe } from '../../shared/pipes/duracao.pipe';
import { PosicaoPipe } from '../../shared/pipes/posicao.pipe';
import { ItemCorrecaoComponent } from './item-correcao/item-correcao.component';

@Component({
  selector: 'app-resultado',
  standalone: true,
  imports: [MarcaComponent, AvisoComponent, ItemCorrecaoComponent, DuracaoPipe, PosicaoPipe],
  templateUrl: './resultado.component.html',
  styleUrl: './resultado.component.scss',
})
export class ResultadoComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly partidaService = inject(PartidaService);
  private readonly rankingService = inject(RankingService);
  private readonly auth = inject(AuthService);

  readonly carregando = signal(true);
  readonly erro = signal<string | null>(null);
  readonly resultado = signal<ResultadoPartida | null>(null);
  readonly minhaPosicao = signal<RankingItem | null>(null);

  ngOnInit(): void {
    const parametro = this.route.snapshot.paramMap.get('partidaId');
    const partidaId = Number(parametro);
    if (!parametro || !Number.isInteger(partidaId) || partidaId <= 0) {
      void this.router.navigate(['/jogo']);
      return;
    }
    this.carregar(partidaId);
  }

  private carregar(partidaId: number): void {
    this.carregando.set(true);
    this.erro.set(null);
    this.partidaService.obterResultado(partidaId).subscribe({
      next: (resultado) => {
        this.resultado.set(resultado);
        this.carregando.set(false);
        this.rankingService.obterMeuResultado().subscribe({
          next: (posicao) => this.minhaPosicao.set(posicao),
          error: () => {
            // A posição é complementar; a correção não depende dela.
          },
        });
      },
      error: (erro: unknown) => {
        this.carregando.set(false);
        if (erro instanceof HttpErrorResponse && (erro.status === 404 || erro.status === 409)) {
          void this.router.navigate(['/jogo']);
          return;
        }
        this.erro.set(mensagemErro(erro));
      },
    });
  }

  formatarPercentual(valor: number): string {
    return `${valor.toFixed(1).replace('.', ',')}%`;
  }

  verRanking(): void {
    void this.router.navigate(['/ranking']);
  }

  jogarNovamente(): void {
    this.partidaService.limparEstado();
    void this.router.navigate(['/jogo']);
  }

  sair(): void {
    this.auth.logout();
  }
}
