import { environment } from '../../../environments/environment';

export const AVISO_API_INDISPONIVEL =
  'Esta é uma prévia pública da interface. A API do jogo ainda não foi publicada; por isso, não é possível concluir o login, iniciar partidas, ver resultados ou consultar o ranking. Nenhum resultado é simulado. Procure o professor para usar a versão completa.';

export const MENSAGEM_API_INDISPONIVEL =
  'A API do jogo não está configurada nesta publicação. A operação não pode ser concluída e nenhum resultado é simulado. Procure o professor.';

export function apiConfigurada(): boolean {
  return environment.apiUrl.trim().length > 0;
}

export class ApiIndisponivelError extends Error {
  constructor() {
    super(MENSAGEM_API_INDISPONIVEL);
    this.name = 'ApiIndisponivelError';
  }
}
