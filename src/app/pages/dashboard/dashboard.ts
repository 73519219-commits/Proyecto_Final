import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { TarjetasComponent } from '../../components/tarjetas/tarjetas';
import { DonacionService } from '../../services/donacion';
import { SolicitudService } from '../../services/solicitud';
import { UsuarioService } from '../../services/usuario';
import { VoluntarioService } from '../../services/voluntario';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, TarjetasComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class DashboardComponent {
  private readonly usuarioService = inject(UsuarioService);
  private readonly donacionService = inject(DonacionService);
  private readonly solicitudService = inject(SolicitudService);
  private readonly voluntarioService = inject(VoluntarioService);

  readonly usuarioActual = this.usuarioService.usuarioActual;
  readonly tipoUsuario = computed(() => this.usuarioActual()?.tipo ?? 'Visitante');

  readonly resumen = computed(() => [
    {
      titulo: 'Usuarios',
      valor: this.usuarioService.totalUsuarios(),
      descripcion: 'Total del sistema',
      color: 'success',
      icono: '👥',
    },
    {
      titulo: 'Donaciones',
      valor: this.donacionService.donaciones().length,
      descripcion: 'Alimentos registrados',
      color: 'warning',
      icono: '📦',
    },
    {
      titulo: 'Solicitudes',
      valor: this.solicitudService.solicitudes().length,
      descripcion: 'Solicitudes activas',
      color: 'success',
      icono: '✅',
    },
    {
      titulo: 'Entregas',
      valor: this.voluntarioService.entregas().length,
      descripcion: 'Pendientes y asignadas',
      color: 'primary',
      icono: '🚚',
    }
  ]);
}
