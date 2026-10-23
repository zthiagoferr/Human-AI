import { CartaPublica, Escolha } from './carta.models';

export interface Partida {
  id: number;
  iniciadaEm: string;
  totalPerguntas: number;
  cartas: CartaPublica[];
}

export interface PartidaResponse {
  partida: Partida | null;
}

export interface RespostaItem {
  cartaId: string;
  escolha: Escolha;
}

export interface CorrecaoItem {
  numero: number;
  cartaId: string;
  citacao: string;
  categoria: string;
  tema: string;
  escolhaAluno: Escolha;
  respostaCorreta: Escolha;
  acertou: boolean;
  analise: string;
}

export interface ResultadoPartida {
  partidaId: number;
  totalPerguntas: number;
  acertos: number;
  erros: number;
  percentual: number;
  duracaoMs: number;
  iniciadaEm: string;
  concluidaEm: string;
  correcao: CorrecaoItem[];
}
