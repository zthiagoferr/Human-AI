export type Papel = 'aluno' | 'professor';

export interface Usuario {
  id: number;
  nome: string;
  usuario: string;
}

export interface SessaoResponse {
  usuario: Usuario;
  papel: Papel;
}

export type UsuarioResponse = SessaoResponse;

export interface RegistroPayload {
  nome: string;
  email: string;
  senha: string;
}

export interface LoginPayload {
  email: string;
  senha: string;
}
