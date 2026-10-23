import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { RankingService } from './ranking.service';

describe('RankingService', () => {
  let service: RankingService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(RankingService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('deve carregar o ranking', () => {
    service.carregar(500, 0).subscribe((dados) => {
      expect(dados.totalParticipantes).toBe(1);
      expect(dados.itens[0].nome).toBe('Ana');
    });

    const req = http.expectOne(
      (r) => r.url === 'http://localhost:8000/api/ranking' && r.params.get('limite') === '500',
    );
    req.flush({
      atualizadoEm: '2026-10-23T14:00:00+00:00',
      totalParticipantes: 1,
      limite: 500,
      offset: 0,
      itens: [
        {
          posicao: 1,
          usuarioId: 1,
          nome: 'Ana',
          acertos: 22,
          erros: 0,
          duracaoMs: 1000,
          concluidaEm: '2026-10-23T14:00:00+00:00',
        },
      ],
      meuResultado: null,
    });

    expect(service.dados()?.itens.length).toBe(1);
  });
});
