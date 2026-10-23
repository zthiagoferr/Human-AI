import { HttpErrorResponse } from '@angular/common/http';

import { ErroApi, ErroDetalhe } from '../models/erro-api.model';

export function mensagemErro(erro: unknown): string {
  if (erro instanceof HttpErrorResponse) {
    if (erro.status === 0) {
      return 'Não foi possível conectar ao servidor. Verifique se o back-end está rodando em http://localhost:8000.';
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
  return 'Não foi possível concluir a operação. Tente novamente.';
}
