import { HttpClient } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { finalize, map, Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { RankingItem, RankingResponse } from '../models/ranking.models';
import { mensagemErro } from '../utils/erro';

@Injectable({ providedIn: 'root' })
export class RankingService {
  private readonly api = `${environment.apiUrl}/ranking`;
  private readonly _dados = signal<RankingResponse | null>(null);
  private readonly _carregando = signal(false);
  private readonly _erro = signal<string | null>(null);
  private readonly _revisao = signal(0);

  readonly dados = this._dados.asReadonly();
  readonly carregando = this._carregando.asReadonly();
  readonly erro = this._erro.asReadonly();
  readonly revisao = this._revisao.asReadonly();

  constructor(private readonly http: HttpClient) {}

  carregar(
    limite: number = environment.rankingLimite,
    offset = 0,
  ): Observable<RankingResponse> {
    this._carregando.set(true);
    this._erro.set(null);
    return this.http
      .get<RankingResponse>(this.api, { params: { limite, offset } })
      .pipe(
        tap((dados) => this._dados.set(dados)),
        tap({ error: (erro: unknown) => this._erro.set(mensagemErro(erro)) }),
        finalize(() => this._carregando.set(false)),
      );
  }

  obterMeuResultado(): Observable<RankingItem | null> {
    return this.http
      .get<RankingResponse>(this.api, { params: { limite: 1, offset: 0 } })
      .pipe(map((resposta) => resposta.meuResultado));
  }

  notificarConclusao(): void {
    this._revisao.update((valor) => valor + 1);
    this.carregar(environment.rankingLimite, 0).subscribe({
      error: () => {
        // O prefetch é best-effort; a tela de ranking tentará novamente.
      },
    });
  }

  limpar(): void {
    this._dados.set(null);
    this._erro.set(null);
    this._carregando.set(false);
    this._revisao.set(0);
  }
}
