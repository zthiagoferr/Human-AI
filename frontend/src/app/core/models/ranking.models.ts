export interface RankingItem {
  posicao: number;
  usuarioId: number;
  nome: string;
  acertos: number;
  erros: number;
  duracaoMs: number;
  concluidaEm: string;
}

export interface RankingResponse {
  atualizadoEm: string;
  totalParticipantes: number;
  limite: number;
  offset: number;
  itens: RankingItem[];
  meuResultado: RankingItem | null;
}
