import { Component, input } from '@angular/core';

@Component({
  selector: 'app-marca',
  standalone: true,
  templateUrl: './marca.component.html',
  styleUrl: './marca.component.scss',
})
export class MarcaComponent {
  readonly tamanho = input<'grande' | 'compacto'>('compacto');
}
