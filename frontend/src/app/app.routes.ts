import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';
import { guestGuard } from './core/auth/guest.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'registrar',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/registro/registro.component').then((m) => m.RegistroComponent),
  },
  {
    path: 'recuperar-senha',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/recuperar-senha/recuperar-senha.component').then(
        (m) => m.RecuperarSenhaComponent,
      ),
  },
  {
    path: 'jogo',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/jogo/jogo.component').then((m) => m.JogoComponent),
  },
  {
    path: 'resultado/:partidaId',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/resultado/resultado.component').then(
        (m) => m.ResultadoComponent,
      ),
  },
  {
    path: 'ranking',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/ranking/ranking.component').then((m) => m.RankingComponent),
  },
  {
    path: 'vincular-legado',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/vincular-legado/vincular-legado.component').then(
        (m) => m.VincularLegadoComponent,
      ),
  },
  { path: '**', redirectTo: '' },
];
