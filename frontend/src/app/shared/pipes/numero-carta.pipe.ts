import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'numeroCarta', standalone: true })
export class NumeroCartaPipe implements PipeTransform {
  transform(valor: number): string {
    return `#${String(valor).padStart(2, '0')}`;
  }
}
