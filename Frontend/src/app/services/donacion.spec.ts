import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { authInterceptor } from '../core/interceptors/auth.interceptor';
import { Donacion } from '../models/donacion';
import { DonacionService } from './donacion';

describe('DonacionService', () => {
  let service: DonacionService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(DonacionService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('adjunta el Bearer y mapea la respuesta del backend', () => {
    TestBed.inject(TokenStorageService).guardar('token-demo');
    let resultado: Donacion[] = [];

    service.listar().subscribe((donaciones) => {
      resultado = donaciones;
    });

    const peticion = http.expectOne((req) => req.url.endsWith('/donaciones/'));
    expect(peticion.request.method).toBe('GET');
    expect(peticion.request.headers.get('Authorization')).toBe('Bearer token-demo');

    peticion.flush([
      {
        id: 1,
        nombre_alimento: 'Pan de trigo',
        descripcion: 'Pan recién horneado',
        cantidad: 40,
        unidad: 'unidad',
        fecha_vencimiento: '2026-12-01',
        direccion_recojo: 'Av. Real 320',
        hora_disponible: '08:00 - 10:00',
        estado: 'disponible',
        usuario_negocio_id: 2,
      },
    ]);

    expect(resultado.length).toBe(1);
    expect(resultado[0].nombreAlimento).toBe('Pan de trigo');
    expect(resultado[0].estado).toBe('Disponible');
    expect(service.donaciones().length).toBe(1);

    TestBed.inject(TokenStorageService).limpiar();
    expect(service.donaciones()).toEqual([]);
  });
});
