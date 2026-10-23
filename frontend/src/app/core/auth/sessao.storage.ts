import { Injectable } from '@angular/core';

const CHAVE_TOKEN_LEGADO = 'humanai.token';
const PREFIXO_RESPOSTAS = 'humanai.respostas.';

@Injectable({ providedIn: 'root' })
export class SessaoStorage {
  limparTokenLegado(): void {
    try {
      sessionStorage.removeItem(CHAVE_TOKEN_LEGADO);
    } catch {
      // Armazenamento indisponível.
    }
  }

  limparRespostas(): void {
    try {
      const chaves = Array.from({ length: sessionStorage.length }, (_, i) =>
        sessionStorage.key(i),
      ).filter((chave): chave is string => !!chave?.startsWith(PREFIXO_RESPOSTAS));
      for (const chave of chaves) {
        sessionStorage.removeItem(chave);
      }
    } catch {
      // Armazenamento indisponível.
    }
  }
}
