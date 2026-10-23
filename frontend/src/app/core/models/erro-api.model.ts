export interface ErroDetalhe {
  campo?: string | null;
  mensagem: string;
}

export interface ErroApi {
  erro: {
    codigo: string;
    mensagem: string;
    detalhes?: ErroDetalhe[] | Record<string, unknown> | null;
  };
}
