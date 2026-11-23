import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { SolicitudService } from './solicitud';

describe('SolicitudService', () => {
  let service: SolicitudService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SolicitudService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('actualiza la cantidad de una solicitud con PUT', () => {
    let resultado: number | undefined;
    service.actualizar(7, { cantidad_solicitada: 4 }).subscribe((solicitud) => {
      resultado = solicitud.cantidadSolicitada;
    });

    const request = http.expectOne((req) => req.url.endsWith('/solicitudes/7'));
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({ cantidad_solicitada: 4 });
    request.flush({
      id: 7,
      donacion_id: 3,
      comedor_id: 2,
      cantidad_solicitada: 4,
      estado: 'pendiente',
    });

    expect(resultado).toBe(4);
    TestBed.inject(TokenStorageService).limpiar();
    expect(service.solicitudes()).toEqual([]);
  });
});
