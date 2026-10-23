import { Component, DestroyRef, inject, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { catchError, exhaustMap, of, timer } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';
import { RankingItem } from '../../core/models/ranking.models';
import { PartidaService } from '../../core/services/partida.service';
import { RankingService } from '../../core/services/ranking.service';
import { formatarDataHora } from '../../core/utils/tempo';
import { environment } from '../../../environments/environment';
import { AvisoComponent } from '../../shared/components/aviso/aviso.component';
import { MarcaComponent } from '../../shared/components/marca/marca.component';
import { DuracaoPipe } from '../../shared/pipes/duracao.pipe';
import { PosicaoPipe } from '../../shared/pipes/posicao.pipe';

@Component({
  selector: 'app-ranking',
  standalone: true,
  imports: [MarcaComponent, AvisoComponent, DuracaoPipe, PosicaoPipe],
  templateUrl: './ranking.component.html',
  styleUrl: './ranking.component.scss',
})
export class RankingComponent implements OnInit {
  private readonly rankingService = inject(RankingService);
  private readonly partidaService = inject(PartidaService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly dados = this.rankingService.dados;
  readonly carregando = this.rankingService.carregando;
  readonly erro = this.rankingService.erro;

  ngOnInit(): void {
    timer(0, environment.rankingPollMs)
      .pipe(
        exhaustMap(() =>
          document.hidden
            ? of(null)
            : this.rankingService
                .carregar(environment.rankingLimite, 0)
                .pipe(catchError(() => of(null))),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe();

    const aoMudarVisibilidade = () => {
      if (!document.hidden) {
        this.atualizarAgora();
      }
    };
    document.addEventListener('visibilitychange', aoMudarVisibilidade);
    this.destroyRef.onDestroy(() =>
      document.removeEventListener('visibilitychange', aoMudarVisibilidade),
    );
  }

  atualizarAgora(): void {
    this.rankingService
      .carregar(environment.rankingLimite, 0)
      .pipe(catchError(() => of(null)))
      .subscribe();
  }

  atualizadoEm(): string {
    return formatarDataHora(this.dados()?.atualizadoEm ?? '');
  }

  ehMeu(item: RankingItem): boolean {
    return item.usuarioId === this.dados()?.meuResultado?.usuarioId;
  }

  jogarNovamente(): void {
    this.partidaService.limparEstado();
    void this.router.navigate(['/jogo']);
  }

  sair(): void {
    this.auth.logout();
  }
}
