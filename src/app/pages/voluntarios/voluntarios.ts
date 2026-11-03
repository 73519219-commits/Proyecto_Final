import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { DonacionService } from '../../services/donacion';
import { VoluntarioService } from '../../services/voluntario';

@Component({
  selector: 'app-voluntarios',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './voluntarios.html',
  styleUrl: './voluntarios.css',
})
export class VoluntariosComponent {
  private readonly donacionService = inject(DonacionService);
  private readonly voluntarioService = inject(VoluntarioService);

  readonly donaciones = this.donacionService.donaciones;
  readonly voluntarios = this.voluntarioService.voluntarios;
  readonly entregas = this.voluntarioService.entregas;

  aceptarEntrega(id: number): void {
    this.voluntarioService.aceptarEntrega(id);
  }

  cambiarEstado(id: number, estado: 'Pendiente' | 'En tránsito' | 'Entregada' | 'Cancelada'): void {
    this.voluntarioService.cambiarEstadoEntrega(id, estado);
  }
}
