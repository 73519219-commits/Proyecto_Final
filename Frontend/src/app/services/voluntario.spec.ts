import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { API_BASE_URL } from '../core/api.config';
import { EntregaDto } from '../models/api/entrega.dto';
import { VoluntarioService } from './voluntario';

describe('VoluntarioService', () => {
  let service: VoluntarioService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(VoluntarioService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('mantiene una misión aceptada aunque la recarga de misiones abiertas no la incluya', () => {
    const baseUrl = TestBed.inject(API_BASE_URL);
    service.listarAbiertas().subscribe();
    http.expectOne(`${baseUrl}/voluntarios/entregas/abiertas`).flush([
      entrega(12, 'abierta'),
    ]);

    service.listarEntregas().subscribe();
    http.expectOne(`${baseUrl}/voluntarios/entregas`).flush([]);

    service.aceptarEntrega(12).subscribe();
    http.expectOne(`${baseUrl}/voluntarios/entregas/12/aceptar`).flush(
      entrega(12, 'aceptada', 4),
    );

    service.listarAbiertas().subscribe();
    http.expectOne(`${baseUrl}/voluntarios/entregas/abiertas`).flush([]);

    expect(service.entregas()).toEqual([
      expect.objectContaining({ id: 12, estado: 'Aceptada', voluntarioId: 4 }),
    ]);
  });

  it('actualiza la misión asignada al marcarla recogida', () => {
    const baseUrl = TestBed.inject(API_BASE_URL);
    service.aceptarEntrega(12).subscribe();
    http.expectOne(`${baseUrl}/voluntarios/entregas/12/aceptar`).flush(
      entrega(12, 'aceptada', 4),
    );

    service.marcarRecogido(12).subscribe();
    http.expectOne(`${baseUrl}/voluntarios/entregas/12/recogido`).flush(
      entrega(12, 'recogida', 4),
    );

    expect(service.entregas()[0]).toEqual(
      expect.objectContaining({ id: 12, estado: 'Recogida' }),
    );
  });

  it('limpia las misiones al invalidar la sesión', () => {
    const baseUrl = TestBed.inject(API_BASE_URL);
    service.aceptarEntrega(12).subscribe();
    http.expectOne(`${baseUrl}/voluntarios/entregas/12/aceptar`).flush(
      entrega(12, 'aceptada', 4),
    );

    TestBed.inject(TokenStorageService).limpiar();
    expect(service.entregas()).toEqual([]);
  });
});

function entrega(
  id: number,
  estado: EntregaDto['estado'],
  voluntario_id = 0,
): EntregaDto {
  return {
    id,
    solicitud_id: id + 100,
    voluntario_id,
    fecha_asignacion: '2026-11-22',
    fecha_entrega: null,
    estado,
    observaciones: null,
    tipo_apoyo: 'ambos',
  };
}
