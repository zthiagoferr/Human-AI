export type Origem = 'humano' | 'ia';
export type Escolha = Origem;

export interface CartaPublica {
  id: string;
  numero: number;
  citacao: string;
  categoria: string;
  tema: string;
}
