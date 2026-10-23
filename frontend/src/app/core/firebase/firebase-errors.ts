import { mensagemErro } from '../utils/erro';

function codigoDe(erro: unknown): string | null {
  if (
    erro &&
    typeof erro === 'object' &&
    'code' in erro &&
    typeof (erro as { code: unknown }).code === 'string'
  ) {
    const codigo = (erro as { code: string }).code;
    return codigo.startsWith('auth/') ? codigo : null;
  }
  return null;
}

const MENSAGENS: Record<string, string> = {
  'auth/invalid-credential': 'E-mail ou senha inválidos.',
  'auth/wrong-password': 'E-mail ou senha inválidos.',
  'auth/user-not-found': 'E-mail ou senha inválidos.',
  'auth/invalid-email': 'Informe um e-mail válido.',
  'auth/email-already-in-use':
    'Este e-mail já está cadastrado. Tente entrar ou recuperar a senha.',
  'auth/weak-password': 'A senha não atende aos requisitos.',
  'auth/too-many-requests':
    'Muitas tentativas. Aguarde alguns minutos e tente novamente.',
  'auth/network-request-failed':
    'Não foi possível conectar ao serviço de autenticação. Verifique sua conexão.',
  'auth/user-disabled': 'Esta conta foi desativada. Procure o professor.',
  'auth/operation-not-allowed':
    'O login por e-mail e senha não está habilitado no Firebase.',
  'auth/invalid-api-key':
    'A configuração do Firebase está incompleta. Procure o professor.',
  'auth/configuration-not-found':
    'A configuração do Firebase está incompleta. Procure o professor.',
  'auth/requires-recent-login':
    'Por segurança, entre novamente para continuar.',
};

export function mensagemErroAuth(erro: unknown): string {
  const codigo = codigoDe(erro);
  if (codigo && MENSAGENS[codigo]) {
    return MENSAGENS[codigo];
  }
  if (erro instanceof Error && !('code' in erro) && erro.message) {
    return erro.message;
  }
  return mensagemErro(erro);
}

export function ehErroUsuarioNaoEncontrado(erro: unknown): boolean {
  return codigoDe(erro) === 'auth/user-not-found';
}
