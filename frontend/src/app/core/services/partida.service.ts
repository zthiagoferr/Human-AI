import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';
import { catchError, map, Observable, of, switchMap, tap, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Escolha } from '../models/carta.models';
import {
  Partida,
  PartidaResponse,
  RespostaItem,
  ResultadoPartida,
} from '../models/partida.models';

const PREFIXO_RESPOSTAS = 'humanai.respostas.';

@Injectable({ providedIn: 'root' })
export class PartidaService {
  private readonly api = `${environment.apiUrl}/partidas`;
  private readonly _partida = signal<Partida | null>(null);
  private readonly cacheResultados = new Map<number, ResultadoPartida>();

  readonly partida = this._partida.asReadonly();

  constructor(private readonly http: HttpClient) {}

  obterAtual(): Observable<Partida | null> {
    return this.http.get<PartidaResponse>(`${this.api}/atual`).pipe(
      map((resposta) => resposta.partida),
      tap((partida) => this._partida.set(partida)),
    );
  }

  iniciar(): Observable<Partida> {
    return this.http.post<PartidaResponse>(this.api, {}).pipe(
      map((resposta) => {
        if (!resposta.partida) {
          throw new Error('A API não retornou a partida iniciada.');
        }
        return resposta.partida;
      }),
      tap((partida) => this._partida.set(partida)),
    );
  }

  obterOuIniciar(): Observable<Partida> {
    if (this._partida()) {
      return of(this._partida() as Partida);
    }
    return this.obterAtual().pipe(
      switchMap((partida) => (partida ? of(partida) : this.iniciar())),
      catchError((erro: unknown) => {
        if (erro instanceof HttpErrorResponse && erro.status === 409) {
          return this.obterAtual().pipe(
            map((partida) => {
              if (!partida) {
                throw erro;
              }
              return partida;
            }),
          );
        }
        return throwError(() => erro);
      }),
    );
  }

  abandonar(partidaId: number): Observable<void> {
    return this.http.post<void>(`${this.api}/${partidaId}/abandonar`, {}).pipe(
      tap(() => {
        this._partida.set(null);
        this.removerRespostas(partidaId);
      }),
    );
  }

  enviarRespostas(
    partidaId: number,
    respostas: RespostaItem[],
  ): Observable<ResultadoPartida> {
    return this.http
      .post<ResultadoPartida>(`${this.api}/${partidaId}/respostas`, { respostas })
      .pipe(
        tap((resultado) => {
          this.cacheResultados.set(resultado.partidaId, resultado);
          this._partida.set(null);
          this.removerRespostas(resultado.partidaId);
        }),
      );
  }

  obterResultado(partidaId: number): Observable<ResultadoPartida> {
    const emCache = this.cacheResultados.get(partidaId);
    if (emCache) {
      return of(emCache);
    }
    return this.http
      .get<ResultadoPartida>(`${this.api}/${partidaId}/resultado`)
      .pipe(tap((resultado) => this.cacheResultados.set(partidaId, resultado)));
  }

  salvarRespostas(
    partidaId: number,
    respostas: Record<string, Escolha | null>,
  ): void {
    try {
      sessionStorage.setItem(
        `${PREFIXO_RESPOSTAS}${partidaId}`,
        JSON.stringify(respostas),
      );
    } catch {
      // Armazenamento indisponível: segue apenas em memória.
    }
  }

  lerRespostas(partidaId: number): Record<string, Escolha | null> {
    try {
      const bruto = sessionStorage.getItem(`${PREFIXO_RESPOSTAS}${partidaId}`);
      return bruto ? (JSON.parse(bruto) as Record<string, Escolha | null>) : {};
    } catch {
      return {};
    }
  }

  removerRespostas(partidaId: number): void {
    try {
      sessionStorage.removeItem(`${PREFIXO_RESPOSTAS}${partidaId}`);
    } catch {
      // ignora
    }
  }

  limparEstado(): void {
    this._partida.set(null);
    this.cacheResultados.clear();
  }
}
