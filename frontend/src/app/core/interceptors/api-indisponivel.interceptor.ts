import { HttpInterceptorFn } from '@angular/common/http';
import { throwError } from 'rxjs';

import { ApiIndisponivelError, apiConfigurada } from '../utils/api';

const CAMINHOS_API = /^\/(auth|partidas|ranking)(\/|$)/;

export const apiIndisponivelInterceptor: HttpInterceptorFn = (
  requisicao,
  proximo,
) => {
  if (!apiConfigurada() && CAMINHOS_API.test(requisicao.url)) {
    return throwError(() => new ApiIndisponivelError());
  }
  return proximo(requisicao);
};
