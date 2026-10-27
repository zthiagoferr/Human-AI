import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import {
  catchError,
  firstValueFrom,
  from,
  map,
  Observable,
  switchMap,
  tap,
  throwError,
  timeout,
} from 'rxjs';

import { environment } from '../../../environments/environment';
import { FirebaseAuthGateway } from '../firebase/firebase-auth.gateway';
import {
  LoginPayload,
  RegistroPayload,
  SessaoResponse,
  Usuario,
} from '../models/auth.models';
import { PartidaService } from '../services/partida.service';
import { RankingService } from '../services/ranking.service';
import { ApiIndisponivelError, apiConfigurada } from '../utils/api';
import { SessaoStorage } from './sessao.storage';
import { SessaoStore } from './sessao.store';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = `${environment.apiUrl}/auth`;
  private cancelarObservacao: (() => void) | null = null;

  constructor(
    private readonly http: HttpClient,
    private readonly store: SessaoStore,
    private readonly storage: SessaoStorage,
    private readonly router: Router,
    private readonly gateway: FirebaseAuthGateway,
    private readonly partidaService: PartidaService,
    private readonly rankingService: RankingService,
  ) {}

  async inicializar(): Promise<void> {
    this.storage.limparTokenLegado();

    if (!apiConfigurada()) {
      this.store.limpar();
      this.store.marcarPronto();
      return;
    }

    try {
      await this.gateway.configurarPersistencia();
    } catch {
      // O SDK segue com a persistência padrão.
    }

    try {
      this.cancelarObservacao?.();
      this.cancelarObservacao = this.gateway.observar((usuario) => {
        this.store.definirAutenticado(!!usuario);
        if (!usuario) {
          this.store.limpar();
        }
      });
    } catch {
      // Configuração incompleta: a tela de login mostrará a mensagem.
    }

    try {
      const usuario = await this.gateway.aguardarPronto();
      if (!usuario) {
        this.store.marcarPronto();
        return;
      }
      this.store.definirAutenticado(true);
      await firstValueFrom(this.sincronizarSessao().pipe(timeout(4000)));
    } catch (erro: unknown) {
      if (this.ehNaoAutorizado(erro)) {
        this.store.limpar();
      }
    } finally {
      this.store.marcarPronto();
    }
  }

  registrar(dados: RegistroPayload): Observable<Usuario> {
    if (!apiConfigurada()) {
      return throwError(() => new ApiIndisponivelError());
    }

    return from(this.gateway.criar(dados.email, dados.senha, dados.nome)).pipe(
      switchMap(() =>
        this.http.post<SessaoResponse>(`${this.api}/sessao`, { nome: dados.nome }),
      ),
      tap((resposta) => this.aplicarSessao(resposta)),
      map((resposta) => resposta.usuario),
      catchError((erro: unknown) => {
        void this.gateway.sair().catch(() => undefined);
        this.store.limpar();
        return throwError(() => erro);
      }),
    );
  }

  login(dados: LoginPayload): Observable<Usuario> {
    if (!apiConfigurada()) {
      return throwError(() => new ApiIndisponivelError());
    }

    return from(this.gateway.entrar(dados.email, dados.senha)).pipe(
      switchMap(() => this.sincronizarSessao()),
      map((resposta) => resposta.usuario),
      catchError((erro: unknown) => {
        void this.gateway.sair().catch(() => undefined);
        this.store.limpar();
        return throwError(() => erro);
      }),
    );
  }

  recuperarSenha(email: string): Observable<void> {
    return from(this.gateway.recuperarSenha(email));
  }

  vincularLegado(codigo: string): Observable<Usuario> {
    if (!apiConfigurada()) {
      return throwError(() => new ApiIndisponivelError());
    }

    return this.http
      .post<SessaoResponse>(`${this.api}/vincular-legado`, { codigo })
      .pipe(
        tap((resposta) => this.aplicarSessao(resposta)),
        map((resposta) => resposta.usuario),
      );
  }

  logout(): void {
    void this.encerrarSessao();
  }

  private sincronizarSessao(): Observable<SessaoResponse> {
    return this.http.get<SessaoResponse>(`${this.api}/me`).pipe(
      tap((resposta) => this.aplicarSessao(resposta)),
    );
  }

  private aplicarSessao(resposta: SessaoResponse): void {
    this.limparEstadoDeJogo();
    this.store.definirSessao(resposta.usuario, resposta.papel);
  }

  private async encerrarSessao(): Promise<void> {
    try {
      await this.gateway.sair();
    } catch {
      // O estado local é limpo mesmo se o SDK falhar.
    } finally {
      this.cancelarObservacao?.();
      this.cancelarObservacao = null;
      this.limparEstadoDeJogo();
      this.store.limpar();
      await this.router.navigate(['/login']);
    }
  }

  private limparEstadoDeJogo(): void {
    this.partidaService.limparEstado();
    this.rankingService.limpar();
  }

  private ehNaoAutorizado(erro: unknown): boolean {
    return (
      !!erro &&
      typeof erro === 'object' &&
      'status' in erro &&
      (erro as { status: unknown }).status === 401
    );
  }
}
