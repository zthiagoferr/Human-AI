import { Component, input } from '@angular/core';

import { CartaPublica } from '../../../core/models/carta.models';
import { NumeroCartaPipe } from '../../../shared/pipes/numero-carta.pipe';

@Component({
  selector: 'app-carta',
  standalone: true,
  imports: [NumeroCartaPipe],
  templateUrl: './carta.component.html',
  styleUrl: './carta.component.scss',
})
export class CartaComponent {
  readonly carta = input.required<CartaPublica>();
  readonly posicao = input.required<number>();
  readonly total = input.required<number>();
}
