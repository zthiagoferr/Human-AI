import { Component, input } from '@angular/core';

import { CorrecaoItem } from '../../../core/models/partida.models';
import { NumeroCartaPipe } from '../../../shared/pipes/numero-carta.pipe';

@Component({
  selector: 'app-item-correcao',
  standalone: true,
  imports: [NumeroCartaPipe],
  templateUrl: './item-correcao.component.html',
  styleUrl: './item-correcao.component.scss',
})
export class ItemCorrecaoComponent {
  readonly item = input.required<CorrecaoItem>();

  rotulo(valor: string): string {
    return valor === 'humano' ? 'Humano' : 'IA';
  }
}
