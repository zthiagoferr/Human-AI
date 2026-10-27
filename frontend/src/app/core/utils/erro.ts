import { HttpErrorResponse } from '@angular/common/http';

import { ErroApi, ErroDetalhe } from '../models/erro-api.model';

export function mensagemErro(erro: unknown): string {
  if (erro instanceof HttpErrorResponse) {
    if (erro.status === 0) {
      return 'Não foi possível conectar ao servidor do jogo. Verifique sua conexão e tente novamente.';
    }
    const corpo = erro.error as ErroApi | null;
    const mensagem = corpo?.erro?.mensagem;
    if (mensagem) {
      const detalhes = corpo?.erro?.detalhes;
      if (Array.isArray(detalhes)) {
        const campos = (detalhes as ErroDetalhe[])
          .map((detalhe) => detalhe.mensagem)
          .filter(Boolean)
          .join(' ');
        return campos ? `${mensagem} ${campos}` : mensagem;
      }
      return mensagem;
    }
    if (erro.status === 401) {
      return 'Sessão expirada. Entre novamente.';
    }
    if (erro.status === 500) {
      return 'O servidor encontrou um erro inesperado. Tente novamente.';
    }
  }
  if (erro instanceof Error && erro.message) {
    return erro.message;
  }
  return 'Não foi possível concluir a operação. Tente novamente.';
}
