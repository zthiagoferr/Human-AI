import { Pipe, PipeTransform } from '@angular/core';

import { formatarDuracao } from '../../core/utils/tempo';

@Pipe({ name: 'duracao', standalone: true })
export class DuracaoPipe implements PipeTransform {
  transform(valor: number | null | undefined): string {
    return formatarDuracao(valor ?? 0);
  }
}
