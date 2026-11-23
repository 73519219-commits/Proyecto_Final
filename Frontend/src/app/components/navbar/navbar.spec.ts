import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { NavbarComponent } from './navbar';
import { UsuarioService } from '../../services/usuario';
import { AvisoService } from '../../services/aviso';

describe('Campana de avisos', () => {
  it('marca los avisos como leídos al abrirlos', () => {
    const usuarioActual = signal<any>({
      id: 3,
      tipo: 'Comedor popular',
      nombre: 'Comedor',
    });
    const avisos = signal([
      { id: 8, usuarioDestino: 3, tipo: 'solicitud_aprobada', mensaje: 'Aprobada', referenciaId: 11, leido: false, createdAt: '' },
    ]);
    const marcarLeido = vi.fn(() => of({ ...avisos()[0], leido: true }));

    TestBed.configureTestingModule({
      imports: [NavbarComponent],
      providers: [
        provideRouter([]),
        { provide: UsuarioService, useValue: {
          usuarioActual,
          esAdmin: () => false,
          esNegocio: () => false,
          esComedor: () => true,
          esVoluntario: () => false,
          cerrarSesion: () => undefined,
        } },
        { provide: AvisoService, useValue: {
          avisos,
          listar: () => of(avisos()),
          marcarLeido,
        } },
      ],
    });

    const fixture = TestBed.createComponent(NavbarComponent);
    fixture.detectChanges();
    fixture.componentInstance.abrirAvisos();

    expect(marcarLeido).toHaveBeenCalledWith(8);
  });
});
