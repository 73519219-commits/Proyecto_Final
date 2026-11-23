import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { mensajeError } from '../../core/http/api-error';
import { estadoEntregaDto } from '../../core/mappers/entrega.mapper';
import { EstadoEntrega } from '../../models/voluntario';
import { UsuarioService } from '../../services/usuario';
import { VoluntarioService } from '../../services/voluntario';

@Component({
  selector: 'app-voluntarios',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './voluntarios.html',
  styleUrl: './voluntarios.css',
})
export class VoluntariosComponent implements OnInit {
  private readonly voluntarioService = inject(VoluntarioService);
  private readonly usuarioService = inject(UsuarioService);

  readonly entregas = this.voluntarioService.entregas;
  readonly usuarioActual = this.usuarioService.usuarioActual;
  readonly esAdmin = computed(() =>
    this.usuarioService.esAdmin(this.usuarioService.usuarioActual()?.tipo),
  );
  readonly esVoluntario = computed(() =>
    this.usuarioService.esVoluntario(this.usuarioService.usuarioActual()?.tipo),
  );
  readonly voluntarios = computed(() => {
    if (this.esAdmin()) {
      return this.usuarioService.usuarios().filter((usuario) => usuario.rol === 'voluntario');
    }

    const actual = this.usuarioActual();
    return actual ? [actual] : [];
  });
  readonly mensaje = signal('');
  readonly error = signal('');

  ngOnInit(): void {
    if (this.esVoluntario()) {
      this.voluntarioService.listarAbiertas().subscribe({
        error: (error: unknown) => this.error.set(mensajeError(error)),
      });
      this.voluntarioService.listarEntregas().subscribe({
        error: (error: unknown) => this.error.set(mensajeError(error)),
      });
    } else {
      this.cargarEntregas();
    }

    if (this.esAdmin()) {
      this.usuarioService.listarUsuarios('voluntario').subscribe({
        error: (error: unknown) => this.error.set(mensajeError(error)),
      });
    }
  }

  aceptarEntrega(id: number): void {
    this.mensaje.set('');
    this.error.set('');

    this.voluntarioService.aceptarEntrega(id).subscribe({
      next: () => this.mensaje.set('Entrega aceptada correctamente.'),
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  pasarEntrega(id: number): void {
    this.mensaje.set('');
    this.error.set('');
    this.voluntarioService.pasarEntrega(id).subscribe({
      next: () => this.mensaje.set('Misión pasada correctamente.'),
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  cambiarEstado(id: number, estado: EstadoEntrega): void {
    this.mensaje.set('');
    this.error.set('');

    this.voluntarioService.cambiarEstadoEntrega(id, estadoEntregaDto(estado)).subscribe({
      next: () => this.mensaje.set('Estado de la entrega actualizado.'),
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  private cargarEntregas(): void {
    this.voluntarioService.listarEntregas().subscribe({
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }
}
