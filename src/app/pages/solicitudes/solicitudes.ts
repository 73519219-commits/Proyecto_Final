import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { Donacion } from '../../models/donacion';
import { DonacionService } from '../../services/donacion';
import { SolicitudService } from '../../services/solicitud';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-solicitudes',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './solicitudes.html',
  styleUrl: './solicitudes.css',
})
export class SolicitudesComponent {
  private readonly donacionService = inject(DonacionService);
  private readonly solicitudService = inject(SolicitudService);
  private readonly usuarioService = inject(UsuarioService);

  readonly donaciones = this.donacionService.donaciones;
  readonly solicitudes = this.solicitudService.solicitudes;
  readonly usuarioActual = this.usuarioService.usuarioActual;
  readonly mensaje = signal('');

  solicitarDonacion(donacion: Donacion): void {
    const usuario = this.usuarioActual();
    if (!usuario) {
      this.mensaje.set('Debe iniciar sesión para solicitar una donación.');
      return;
    }

    this.solicitudService.registrarSolicitud({
      id: Date.now(),
      donacionId: donacion.id,
      comedorId: usuario.id,
      comedorNombre: usuario.nombre,
      cantidadSolicitada: donacion.cantidad,
      fechaSolicitud: new Date().toISOString().split('T')[0],
      estado: 'Pendiente',
    });

    this.donacionService.cambiarEstado(donacion.id, 'Reservada');
    this.mensaje.set('Solicitud enviada correctamente.');
  }

  cancelarSolicitud(id: number): void {
    this.solicitudService.cancelarSolicitud(id);
    this.mensaje.set('Solicitud cancelada.');
  }
}
