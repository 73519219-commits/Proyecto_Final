import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { mensajeError } from '../../core/http/api-error';
import { SolicitudCreateDto } from '../../models/api/solicitud.dto';
import { Donacion } from '../../models/donacion';
import { DonacionService } from '../../services/donacion';
import { SolicitudService } from '../../services/solicitud';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-solicitudes',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './solicitudes.html',
  styleUrl: './solicitudes.css',
})
export class SolicitudesComponent implements OnInit {
  private readonly donacionService = inject(DonacionService);
  private readonly solicitudService = inject(SolicitudService);
  private readonly usuarioService = inject(UsuarioService);

  readonly donaciones = this.donacionService.donacionesDisponibles;
  readonly solicitudes = this.solicitudService.solicitudes;
  readonly usuarioActual = this.usuarioService.usuarioActual;
  readonly esAdmin = computed(() =>
    this.usuarioService.esAdmin(this.usuarioService.usuarioActual()?.tipo),
  );
  readonly esComedor = computed(() =>
    this.usuarioService.esComedor(this.usuarioService.usuarioActual()?.tipo),
  );
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly editandoId = signal<number | null>(null);
  readonly tipoApoyoSolicitud = signal<'recoger' | 'trasladar' | 'ambos'>('ambos');
  readonly cantidadEdicion = new FormControl(1, {
    nonNullable: true,
    validators: [Validators.required, Validators.min(1)],
  });

  ngOnInit(): void {
    this.cargarDonaciones();
    this.cargarSolicitudes();
  }

  solicitarDonacion(donacion: Donacion): void {
    this.mensaje.set('');
    this.error.set('');

    const usuario = this.usuarioActual();
    if (!usuario) {
      this.error.set('Debe iniciar sesión para solicitar una donación.');
      return;
    }

    if (!this.esComedor()) {
      this.error.set('Solo un comedor popular puede registrar solicitudes.');
      return;
    }

    const datos: SolicitudCreateDto = {
      donacion_id: donacion.id,
      comedor_id: usuario.id,
      cantidad_solicitada: donacion.cantidad,
      estado: 'pendiente',
      necesita_apoyo: this.tipoApoyoSolicitud(),
    };

    this.solicitudService.crear(datos).subscribe({
      next: () => {
        this.mensaje.set('Solicitud enviada correctamente.');
        this.cargarDonaciones();
        this.cargarSolicitudes();
      },
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  cancelarSolicitud(id: number): void {
    if (!window.confirm('¿Desea cancelar esta solicitud?')) {
      return;
    }

    this.mensaje.set('');
    this.error.set('');
    this.solicitudService.eliminar(id).subscribe({
      next: () => {
        this.mensaje.set('Solicitud cancelada.');
        this.cargarDonaciones();
        this.cargarSolicitudes();
      },
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  editarSolicitud(id: number, cantidad: number): void {
    this.editandoId.set(id);
    this.cantidadEdicion.setValue(cantidad);
    this.cantidadEdicion.markAsPristine();
  }

  guardarEdicionSolicitud(): void {
    const id = this.editandoId();
    if (id === null || this.cantidadEdicion.invalid) {
      this.cantidadEdicion.markAsTouched();
      return;
    }

    this.mensaje.set('');
    this.error.set('');
    this.solicitudService
      .actualizar(id, { cantidad_solicitada: this.cantidadEdicion.value })
      .subscribe({
        next: () => {
          this.editandoId.set(null);
          this.mensaje.set('Solicitud actualizada correctamente.');
        },
        error: (error: unknown) => this.error.set(mensajeError(error)),
      });
  }

  cancelarEdicion(): void {
    this.editandoId.set(null);
  }

  private cargarDonaciones(): void {
    this.donacionService.listarDisponibles().subscribe({
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  private cargarSolicitudes(): void {
    this.solicitudService.listar().subscribe({
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }
}
