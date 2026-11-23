import { TestBed } from '@angular/core/testing';
import { HttpClient } from '@angular/common/http';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { DashboardComponent } from './dashboard';
import { UsuarioService } from '../../services/usuario';
import { DonacionService } from '../../services/donacion';
import { SolicitudService } from '../../services/solicitud';
import { VoluntarioService } from '../../services/voluntario';
import { API_BASE_URL } from '../../core/api.config';

describe('Dashboard por rol', () => {
  const usuarioActual = signal<any>(null);

  const usuarioService = {
    usuarioActual,
    esAdmin: (tipo?: string) => tipo === 'Administrador',
    esNegocio: (tipo?: string) => tipo === 'Negocio',
    esComedor: (tipo?: string) => tipo === 'Comedor popular',
    esVoluntario: (tipo?: string) => tipo === 'Voluntario',
    cargarPerfil: () => of(usuarioActual()),
    listarUsuarios: () => of([]),
    actualizarDisponibilidad: vi.fn((disponible: boolean) => {
      usuarioActual.update((usuario) => usuario ? { ...usuario, disponible } : usuario);
      return of(usuarioActual());
    }),
  };

  const donacionService = {
    donaciones: signal([]),
    donacionesDisponibles: signal([]),
    listar: () => of([]),
    listarDisponibles: () => of([]),
  };

  const solicitudService = {
    solicitudes: signal([]),
    listar: () => of([]),
    crear: () => of({}),
    aprobar: () => of({}),
    rechazar: () => of({}),
  };

  const voluntarioService = {
    entregas: signal([]),
    listarEntregas: vi.fn(() => of([])),
    listarAbiertas: vi.fn(() => of([])),
    aceptarEntrega: vi.fn(() => of({})),
    pasarEntrega: () => of({}),
  };

  beforeEach(() => {
    usuarioActual.set(null);
    vi.mocked(voluntarioService.listarEntregas).mockClear();
    vi.mocked(voluntarioService.listarAbiertas).mockClear();
    TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        { provide: UsuarioService, useValue: usuarioService },
        { provide: DonacionService, useValue: donacionService },
        { provide: SolicitudService, useValue: solicitudService },
        { provide: VoluntarioService, useValue: voluntarioService },
        { provide: HttpClient, useValue: { get: () => of({}) } },
        { provide: API_BASE_URL, useValue: '/api' },
      ],
    });
  });

  it('renderiza KPIs distintos para negocio y comedor', async () => {
    usuarioActual.set({ id: 2, tipo: 'Negocio', nombre: 'Negocio', disponible: false });
    const negocio = TestBed.createComponent(DashboardComponent);
    await negocio.whenStable();
    negocio.detectChanges();
    expect(negocio.nativeElement.textContent).toContain('Publicaciones activas');
    expect(negocio.nativeElement.textContent).not.toContain('Usuarios');

    usuarioActual.set({ id: 3, tipo: 'Comedor popular', nombre: 'Comedor', disponible: false });
    const comedor = TestBed.createComponent(DashboardComponent);
    await comedor.whenStable();
    comedor.detectChanges();
    expect(comedor.nativeElement.textContent).toContain('Disponibles ahora');
  });

  it('el toggle de disponibilidad actualiza el usuario voluntario', () => {
    usuarioActual.set({ id: 4, tipo: 'Voluntario', nombre: 'Voluntario', disponible: false });
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();

    fixture.componentInstance.cambiarDisponibilidad(true);

    expect(usuarioActual().disponible).toBe(true);
  });

  it('carga misiones abiertas y asignadas para el voluntario', () => {
    usuarioActual.set({ id: 4, tipo: 'Voluntario', nombre: 'Voluntario', disponible: true });

    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();

    expect(voluntarioService.listarAbiertas).toHaveBeenCalled();
    expect(voluntarioService.listarEntregas).toHaveBeenCalled();
  });

  it('bloquea aceptar una segunda misión activa', () => {
    usuarioActual.set({ id: 4, tipo: 'Voluntario', nombre: 'Voluntario', disponible: true });
    voluntarioService.entregas.set([
      { id: 9, solicitudId: 11, voluntarioId: 4, estado: 'Aceptada', tipoApoyo: 'recoger' },
      { id: 10, solicitudId: 12, voluntarioId: 0, estado: 'Abierta', tipoApoyo: 'ambos' },
    ] as any);
    const fixture = TestBed.createComponent(DashboardComponent);
    fixture.detectChanges();
    vi.mocked(voluntarioService.aceptarEntrega).mockClear();

    fixture.componentInstance.aceptarMision(10);

    expect(voluntarioService.aceptarEntrega).not.toHaveBeenCalled();
    expect(fixture.componentInstance.operacionMensaje()).toContain('misión activa');
  });
});
