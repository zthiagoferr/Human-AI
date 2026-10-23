import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'posicao', standalone: true })
export class PosicaoPipe implements PipeTransform {
  transform(valor: number): string {
    return `${valor}º`;
  }
}
