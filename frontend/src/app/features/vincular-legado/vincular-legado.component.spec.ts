import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import {
  FakeFirebaseAuthGateway,
  fakeFirebaseProvider,
} from '../../../testing/fake-firebase-auth.gateway';
import { AuthService } from '../../core/auth/auth.service';
import { VincularLegadoComponent } from './vincular-legado.component';

describe('VincularLegadoComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VincularLegadoComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        fakeFirebaseProvider(new FakeFirebaseAuthGateway()),
      ],
    }).compileComponents();
  });

  it('deve exigir código', () => {
    const fixture = TestBed.createComponent(VincularLegadoComponent);
    expect(fixture.componentInstance.form.invalid).toBeTrue();
  });

  it('deve confirmar vínculo', () => {
    const fixture = TestBed.createComponent(VincularLegadoComponent);
    const componente = fixture.componentInstance;
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'vincularLegado').and.returnValue(
      of({ id: 3, nome: 'Ana', usuario: 'ana' }),
    );

    componente.form.setValue({ codigo: 'ABCDE-12345' });
    componente.enviar();

    expect(auth.vincularLegado).toHaveBeenCalledWith('ABCDE-12345');
    expect(componente.concluido()).toBeTrue();
  });
});
