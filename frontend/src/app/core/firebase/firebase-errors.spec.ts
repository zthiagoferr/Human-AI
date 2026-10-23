import { mensagemErroAuth } from './firebase-errors';

describe('mensagemErroAuth', () => {
  const casos: Array<[string, string]> = [
    ['auth/invalid-credential', 'E-mail ou senha inválidos.'],
    ['auth/wrong-password', 'E-mail ou senha inválidos.'],
    ['auth/user-not-found', 'E-mail ou senha inválidos.'],
    ['auth/invalid-email', 'Informe um e-mail válido.'],
    ['auth/email-already-in-use', 'Este e-mail já está cadastrado'],
    ['auth/too-many-requests', 'Muitas tentativas'],
    ['auth/network-request-failed', 'Não foi possível conectar'],
    ['auth/operation-not-allowed', 'não está habilitado'],
    ['auth/invalid-api-key', 'configuração do Firebase está incompleta'],
  ];

  for (const [codigo, trecho] of casos) {
    it(`deve mapear ${codigo}`, () => {
      expect(mensagemErroAuth({ code: codigo })).toContain(trecho);
    });
  }

  it('deve usar fallback para erro desconhecido', () => {
    expect(mensagemErroAuth(new Error('falha'))).toBe('falha');
  });
});
