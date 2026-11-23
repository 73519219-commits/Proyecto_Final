import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { API_BASE_URL } from '../../core/api.config';
import { mensajeError } from '../../core/http/api-error';
import { TarjetasComponent } from '../../components/tarjetas/tarjetas';
import { DonacionService } from '../../services/donacion';
import { SolicitudService } from '../../services/solicitud';
import { UsuarioService } from '../../services/usuario';
import { VoluntarioService } from '../../services/voluntario';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, TarjetasComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent implements OnInit {
  private readonly usuarioService = inject(UsuarioService);
  private readonly donacionService = inject(DonacionService);
  private readonly solicitudService = inject(SolicitudService);
  private readonly voluntarioService = inject(VoluntarioService);
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  readonly resumenBackend = signal<Record<string, number>>({});
  readonly error = signal('');
  readonly disponibilidadCambiando = signal(false);
  readonly operacionMensaje = signal('');
  readonly tipoApoyoComedor = signal<'recoger' | 'trasladar' | 'ambos'>('ambos');
  readonly disponibleHoy = computed(() => this.usuarioActual()?.disponible ?? false);
  readonly siguientePaso = computed(() => {
    const tipo = this.usuarioActual()?.tipo;
    const datos = this.resumenBackend();
    if (this.usuarioService.esNegocio(tipo)) {
      return (datos['solicitudes_por_aprobar'] ?? 0) > 0
        ? 'Revisa las solicitudes recibidas y coordina la entrega.'
        : 'Publica una donación o revisa tus publicaciones activas.';
    }
    if (this.usuarioService.esComedor(tipo)) {
      return (datos['por_confirmar'] ?? 0) > 0
        ? 'Confirma las recepciones que ya fueron recogidas.'
        : 'Solicita una donación disponible para tu comedor.';
    }
    if (this.usuarioService.esVoluntario(tipo)) {
      return (datos['mi_mision_activa'] ?? 0) > 0
        ? 'Continúa con tu misión activa.'
        : 'Activa tu disponibilidad y acepta una misión abierta.';
    }
    return 'Supervisa solicitudes, entregas y voluntarios disponibles.';
  });
  readonly misionesAbiertasVoluntario = computed(() =>
    this.voluntarioService.entregas().filter((entrega) => entrega.estado === 'Abierta'),
  );
  readonly misionActivaVoluntario = computed(() =>
    this.voluntarioService.entregas().find((entrega) =>
      entrega.estado === 'Aceptada' || entrega.estado === 'Recogida',
    ) ?? null,
  );
  readonly entregasPorConfirmar = computed(() =>
    this.voluntarioService.entregas().filter((entrega) => entrega.estado === 'Recogida'),
  );

  readonly usuarioActual = this.usuarioService.usuarioActual;
  readonly tipoUsuario = computed(() => this.usuarioActual()?.tipo ?? 'Visitante');

  readonly resumen = computed(() => {
    const datos = this.resumenBackend();
    const tipo = this.usuarioActual()?.tipo;
    if (this.usuarioService.esNegocio(tipo)) {
      return [
        { titulo: 'Publicaciones activas', valor: datos['publicaciones_activas'] ?? 0, descripcion: 'Disponibles', color: 'success', icono: '📦' },
        { titulo: 'Por aprobar', valor: datos['solicitudes_por_aprobar'] ?? 0, descripcion: 'Solicitudes pendientes', color: 'warning', icono: '✅' },
        { titulo: 'Kg donados este mes', valor: datos['kg_donados_mes'] ?? 0, descripcion: 'Entregados', color: 'success', icono: '⚖️' },
        { titulo: 'Por vencer', valor: datos['por_vencer'] ?? 0, descripcion: 'En menos de 24 h', color: 'danger', icono: '⏰' },
      ];
    }
    if (this.usuarioService.esComedor(tipo)) {
      return [
        { titulo: 'Disponibles ahora', valor: datos['disponibles_ahora'] ?? 0, descripcion: 'Donaciones vigentes', color: 'success', icono: '📦' },
        { titulo: 'Mis solicitudes', valor: datos['mis_solicitudes_activas'] ?? 0, descripcion: 'Activas', color: 'warning', icono: '✅' },
        { titulo: 'Por confirmar', valor: datos['por_confirmar'] ?? 0, descripcion: 'Recepciones recogidas', color: 'primary', icono: '🤝' },
        { titulo: 'Raciones recibidas', valor: datos['raciones_recibidas'] ?? 0, descripcion: 'Cantidad entregada', color: 'success', icono: '🍲' },
      ];
    }
    if (this.usuarioService.esVoluntario(tipo)) {
      return [
        { titulo: 'Disponible hoy', valor: datos['disponible_hoy'] ?? 0, descripcion: 'Estado actual', color: 'success', icono: '🟢' },
        { titulo: 'Misiones abiertas', valor: datos['misiones_abiertas'] ?? 0, descripcion: 'Sin asignar', color: 'primary', icono: '🚚' },
        { titulo: 'Mi misión activa', valor: datos['mi_mision_activa'] ?? 0, descripcion: 'Aceptada o recogida', color: 'warning', icono: '📍' },
        { titulo: 'Kg transportados', valor: datos['kg_transportados'] ?? 0, descripcion: 'Entregados', color: 'success', icono: '⚖️' },
      ];
    }
    return [
      { titulo: 'Donaciones', valor: datos['total_donaciones'] ?? 0, descripcion: 'Totales', color: 'warning', icono: '📦' },
      { titulo: 'Solicitudes', valor: datos['total_solicitudes'] ?? 0, descripcion: 'Totales', color: 'success', icono: '✅' },
      { titulo: 'Entregas', valor: datos['total_entregas'] ?? 0, descripcion: 'Totales', color: 'primary', icono: '🚚' },
      { titulo: 'Voluntarios disponibles', valor: datos['voluntarios_disponibles_hoy'] ?? 0, descripcion: 'Hoy', color: 'success', icono: '👥' },
      { titulo: 'Misiones sin voluntario', valor: datos['misiones_sin_voluntario'] ?? 0, descripcion: 'Abiertas', color: 'danger', icono: '⚠️' },
    ];
  });

  ngOnInit(): void {
    if (this.usuarioActual()) {
      this.usuarioService.cargarPerfil().subscribe({
        error: (error: unknown) => this.mostrarError(error),
      });
      this.refrescarResumen();
    }

    const tipo = this.usuarioActual()?.tipo;

    if (this.usuarioService.esAdmin(tipo)) {
      this.usuarioService.listarUsuarios().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      this.donacionService.listar().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      this.solicitudService.listar().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      this.voluntarioService.listarEntregas().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      return;
    }

    if (this.usuarioService.esNegocio(tipo)) {
      this.donacionService.listar().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      this.solicitudService.listar().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      return;
    }

    if (this.usuarioService.esComedor(tipo)) {
      this.solicitudService.listar().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      this.donacionService.listarDisponibles().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      this.voluntarioService.listarEntregas().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      return;
    }

    if (this.usuarioService.esVoluntario(tipo)) {
      this.voluntarioService.listarAbiertas().subscribe({ error: (error: unknown) => this.mostrarError(error) });
      this.voluntarioService.listarEntregas().subscribe({ error: (error: unknown) => this.mostrarError(error) });
    }
  }

  aprobarSolicitud(id: number): void {
    this.error.set('');
    this.solicitudService.aprobar(id).subscribe({
      next: () => this.refrescarResumen(),
      error: (error: unknown) => this.mostrarError(error),
    });
  }

  rechazarSolicitud(id: number): void {
    this.error.set('');
    this.solicitudService.rechazar(id).subscribe({
      next: () => this.refrescarResumen(),
      error: (error: unknown) => this.mostrarError(error),
    });
  }

  solicitarDonacion(donacionId: number): void {
    const usuario = this.usuarioActual();
    if (!usuario) return;
    const donacion = this.donacionService.donacionesDisponibles().find((item) => item.id === donacionId);
    if (!donacion) return;
    this.solicitudService.crear({
      donacion_id: donacionId,
      comedor_id: usuario.id,
      cantidad_solicitada: donacion.cantidad,
      estado: 'pendiente',
      necesita_apoyo: this.tipoApoyoComedor(),
    }).subscribe({
      next: () => this.refrescarResumen(),
      error: (error: unknown) => this.mostrarError(error),
    });
  }

  cambiarDisponibilidad(disponible: boolean): void {
    this.disponibilidadCambiando.set(true);
    this.usuarioService.actualizarDisponibilidad(disponible).subscribe({
      next: () => {
        this.disponibilidadCambiando.set(false);
        this.refrescarResumen();
      },
      error: (error: unknown) => {
        this.disponibilidadCambiando.set(false);
        this.mostrarError(error);
      },
    });
  }

  aceptarMision(id: number): void {
    if (!this.disponibleHoy()) {
      this.operacionMensaje.set('Active Disponible hoy antes de aceptar una misión.');
      return;
    }
    if (this.misionActivaVoluntario()) {
      this.operacionMensaje.set('Ya tienes una misión activa.');
      return;
    }
    this.voluntarioService.aceptarEntrega(id).subscribe({
      next: () => {
        this.voluntarioService.listarAbiertas().subscribe({
          error: (error: unknown) => this.mostrarError(error),
        });
        this.refrescarResumen();
      },
      error: (error: unknown) => this.mostrarError(error),
    });
  }

  pasarMision(id: number): void {
    this.voluntarioService.pasarEntrega(id).subscribe({
      next: () => {
        this.voluntarioService.listarAbiertas().subscribe({
          error: (error: unknown) => this.mostrarError(error),
        });
        this.refrescarResumen();
      },
      error: (error: unknown) => this.mostrarError(error),
    });
  }

  marcarRecogido(id: number): void {
    this.voluntarioService.marcarRecogido(id).subscribe({
      next: () => this.refrescarResumen(),
      error: (error: unknown) => this.mostrarError(error),
    });
  }

  confirmarEntrega(id: number): void {
    this.voluntarioService.confirmarEntrega(id).subscribe({
      next: () => this.refrescarResumen(),
      error: (error: unknown) => this.mostrarError(error),
    });
  }

  llamarTelefono(telefono: string): string {
    return `tel:${telefono.replace(/[^+\d]/g, '')}`;
  }

  whatsappTelefono(telefono: string): string {
    return `https://wa.me/${telefono.replace(/\D/g, '')}`;
  }

  private refrescarResumen(): void {
    this.http.get<Record<string, number>>(`${this.baseUrl}/dashboard/resumen`).subscribe({
      next: (datos) => {
        this.resumenBackend.set(datos);
        this.error.set('');
      },
      error: (error: unknown) => {
        this.resumenBackend.set({});
        this.mostrarError(error);
      },
    });
  }

  private mostrarError(error: unknown): void {
    this.error.set(mensajeError(error));
  }
}
