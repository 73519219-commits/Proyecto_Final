import {
  HttpClient,
  HttpErrorResponse,
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { API_BASE_URL } from '../api.config';
import { TokenStorageService } from '../auth/token-storage.service';
import { mensajeError } from '../http/api-error';
import { UsuarioService } from '../../services/usuario';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let http: HttpTestingController;
  let router: Router;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('solo adjunta Bearer a URLs de la API', () => {
    TestBed.inject(TokenStorageService).guardar('token-demo');
    let fallo: unknown;

    TestBed.inject(HttpClient)
      .get('https://tercero.example/data')
      .subscribe({ error: (error: unknown) => (fallo = error) });

    const request = http.expectOne('https://tercero.example/data');
    expect(request.request.headers.has('Authorization')).toBe(false);
    request.flush({ error: 'fuera de alcance' }, { status: 500, statusText: 'Error' });
    expect(fallo).toBeInstanceOf(HttpErrorResponse);
  });

  it('limpia la sesión y redirige al login ante un 401 de la API', () => {
    const almacenamiento = TestBed.inject(TokenStorageService);
    const usuarios = TestBed.inject(UsuarioService);
    usuarios.login('usuario@example.com', 'password123').subscribe();
    http.expectOne(`${TestBed.inject(API_BASE_URL)}/auth/login`).flush({
      access_token: 'token-expirado',
      token_type: 'bearer',
      usuario: {
        id: 1,
        nombres: 'Usuario',
        apellidos: 'Prueba',
        correo: 'usuario@example.com',
        telefono: '987654321',
        direccion: 'Jr. Prueba 100',
        rol: 'comedor',
        estado: 'activo',
      },
    });
    expect(usuarios.usuarioActual()?.id).toBe(1);

    TestBed.inject(HttpClient)
      .get(`${TestBed.inject(API_BASE_URL)}/usuarios/me`)
      .subscribe({ error: () => undefined });

    http.expectOne(`${TestBed.inject(API_BASE_URL)}/usuarios/me`).flush(
      { detail: 'Token inválido' },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(almacenamiento.token()).toBeNull();
    expect(usuarios.usuarioActual()).toBeNull();
    expect(localStorage.getItem('alimento_solidario_usuario')).toBeNull();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('presenta un mensaje entendible cuando el backend no responde', () => {
    expect(mensajeError(new HttpErrorResponse({ status: 0 }))).toContain(
      'Verifique que FastAPI esté en ejecución',
    );
  });
});
