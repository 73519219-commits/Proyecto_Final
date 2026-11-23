import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { UsuarioService } from './services/usuario';
import { adminGuard, negocioGuard, comedorGuard, voluntarioGuard } from './app.routes';

describe('guards de rutas', () => {
  let router: Router;
  let usuarioActual: ReturnType<typeof vi.fn<() => { tipo: string } | null>>;
  let esAdmin: ReturnType<typeof vi.fn<(tipo?: string) => boolean>>;
  let esNegocio!: ReturnType<typeof vi.fn<(tipo?: string) => boolean>>;
  let esComedor!: ReturnType<typeof vi.fn<(tipo?: string) => boolean>>;
  let esVoluntario!: ReturnType<typeof vi.fn<(tipo?: string) => boolean>>;

  beforeEach(() => {
    usuarioActual = vi.fn<() => { tipo: string } | null>(() => null);
    esAdmin = vi.fn<(tipo?: string) => boolean>(() => false);
    esNegocio = vi.fn<(tipo?: string) => boolean>(() => false);
    esComedor = vi.fn<(tipo?: string) => boolean>(() => false);
    esVoluntario = vi.fn<(tipo?: string) => boolean>(() => false);
    TestBed.configureTestingModule({
      providers: [
        { provide: UsuarioService, useValue: { usuarioActual, esAdmin, esNegocio, esComedor, esVoluntario } },
      ],
    });
    router = TestBed.inject(Router);
  });

  it('envía usuarios no autenticados al login', () => {
    const resultado = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));

    expect(resultado).toBeInstanceOf(UrlTree);
    expect(router.serializeUrl(resultado as UrlTree)).toBe('/login');
  });

  it('rechaza roles distintos de admin y permite el rol admin', () => {
    usuarioActual.mockReturnValue({ tipo: 'Negocio' });
    let resultado = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));
    expect(router.serializeUrl(resultado as UrlTree)).toBe('/dashboard');

    usuarioActual.mockReturnValue({ tipo: 'Administrador' });
    esAdmin.mockReturnValue(true);
    resultado = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));
    expect(resultado).toBe(true);
  });

  it('permite al negocio entrar a su guard', () => {
    usuarioActual.mockReturnValue({ tipo: 'Negocio' });
    esNegocio.mockReturnValue(true);
    expect(TestBed.runInInjectionContext(() => negocioGuard({} as never, {} as never))).toBe(true);
  });

  it('permite al comedor entrar a su guard', () => {
    usuarioActual.mockReturnValue({ tipo: 'Comedor popular' });
    esComedor.mockReturnValue(true);
    expect(TestBed.runInInjectionContext(() => comedorGuard({} as never, {} as never))).toBe(true);
  });

  it('permite al voluntario entrar a su guard', () => {
    usuarioActual.mockReturnValue({ tipo: 'Voluntario' });
    esVoluntario.mockReturnValue(true);
    expect(TestBed.runInInjectionContext(() => voluntarioGuard({} as never, {} as never))).toBe(true);
  });
});
