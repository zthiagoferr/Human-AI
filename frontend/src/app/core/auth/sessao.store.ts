import { computed, Injectable, signal } from '@angular/core';

import { Papel, Usuario } from '../models/auth.models';
import { SessaoStorage } from './sessao.storage';

@Injectable({ providedIn: 'root' })
export class SessaoStore {
  private readonly _usuario = signal<Usuario | null>(null);
  private readonly _papel = signal<Papel>('aluno');
  private readonly _autenticado = signal(false);
  private readonly _pronto = signal(false);

  readonly usuario = this._usuario.asReadonly();
  readonly papel = this._papel.asReadonly();
  readonly autenticado = this._autenticado.asReadonly();
  readonly pronto = this._pronto.asReadonly();
  readonly professor = computed(() => this._papel() === 'professor');

  constructor(private readonly storage: SessaoStorage) {}

  definirSessao(usuario: Usuario, papel: Papel): void {
    this._usuario.set(usuario);
    this._papel.set(papel);
    this._autenticado.set(true);
  }

  definirUsuario(usuario: Usuario): void {
    this._usuario.set(usuario);
  }

  definirAutenticado(valor: boolean): void {
    this._autenticado.set(valor);
  }

  marcarPronto(): void {
    this._pronto.set(true);
  }

  limpar(): void {
    this.storage.limparRespostas();
    this._usuario.set(null);
    this._papel.set('aluno');
    this._autenticado.set(false);
  }
}
