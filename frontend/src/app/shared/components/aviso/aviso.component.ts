import { Component, input } from '@angular/core';

@Component({
  selector: 'app-aviso',
  standalone: true,
  templateUrl: './aviso.component.html',
  styleUrl: './aviso.component.scss',
})
export class AvisoComponent {
  readonly mensagem = input.required<string>();
  readonly tipo = input<'erro' | 'sucesso' | 'info'>('info');
}
