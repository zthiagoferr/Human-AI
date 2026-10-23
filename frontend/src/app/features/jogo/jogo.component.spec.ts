import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import {
  FakeFirebaseAuthGateway,
  fakeFirebaseProvider,
} from '../../../testing/fake-firebase-auth.gateway';
import { JogoComponent } from './jogo.component';

describe('JogoComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [JogoComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        fakeFirebaseProvider(new FakeFirebaseAuthGateway()),
      ],
    }).compileComponents();
  });

  it('deve criar o componente', () => {
    const fixture = TestBed.createComponent(JogoComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
