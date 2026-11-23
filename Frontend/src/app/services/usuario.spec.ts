import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { Usuario } from '../models/usuario';
import { UsuarioService } from './usuario';

describe('UsuarioService', () => {
  let service: UsuarioService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(UsuarioService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('login envía correo/password, guarda el token y mapea al usuario', () => {
    let resultado: Usuario | undefined;

    service.login('admin@alimentosolidario.pe', 'admin123').subscribe((usuario) => {
      resultado = usuario;
    });

    const peticion = http.expectOne(
      (req) => req.url.endsWith('/auth/login') && req.method === 'POST',
    );
    expect(peticion.request.body).toEqual({
      correo: 'admin@alimentosolidario.pe',
      password: 'admin123',
    });

    peticion.flush({
      access_token: 'token-demo',
      token_type: 'bearer',
      usuario: {
        id: 1,
        nombres: 'Administrador',
        apellidos: 'Sistema',
        correo: 'admin@alimentosolidario.pe',
        telefono: '987654321',
        direccion: 'Jr. Puno 120',
        rol: 'admin',
        estado: 'activo',
      },
    });

    expect(TestBed.inject(TokenStorageService).token()).toBe('token-demo');
    expect(service.usuarioActual()?.tipo).toBe('Administrador');
    expect(resultado?.nombre).toBe('Administrador Sistema');
  });

  it('reconoce los nombres de comedor usados por el backend y el frontend', () => {
    expect(service.esComedor('comedor')).toBe(true);
    expect(service.esComedor('Comedor popular')).toBe(true);
    expect(service.esComedor('Negocio')).toBe(false);
  });
});
