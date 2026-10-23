import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { PartidaService } from './partida.service';

describe('PartidaService', () => {
  let service: PartidaService;
  let http: HttpTestingController;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(PartidaService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('deve retomar a partida ativa', () => {
    service.obterAtual().subscribe((partida) => {
      expect(partida?.id).toBe(7);
      expect(partida?.cartas.length).toBe(1);
      expect(partida?.cartas[0].id).toBe('01');
    });

    const req = http.expectOne('http://localhost:8000/api/partidas/atual');
    expect(req.request.method).toBe('GET');
    req.flush({
      partida: {
        id: 7,
        iniciadaEm: '2026-10-23T14:00:00+00:00',
        totalPerguntas: 22,
        cartas: [
          {
            id: '01',
            numero: 1,
            citacao: 'Citação de teste.',
            categoria: 'Categoria',
            tema: 'Tema',
          },
        ],
      },
    });
  });

  it('deve iniciar quando não houver partida ativa', () => {
    service.obterOuIniciar().subscribe((partida) => expect(partida.id).toBe(8));

    http
      .expectOne('http://localhost:8000/api/partidas/atual')
      .flush({ partida: null });
    const req = http.expectOne('http://localhost:8000/api/partidas');
    expect(req.request.method).toBe('POST');
    req.flush({
      partida: {
        id: 8,
        iniciadaEm: '2026-10-23T14:00:00+00:00',
        totalPerguntas: 22,
        cartas: [],
      },
    });
  });
});
