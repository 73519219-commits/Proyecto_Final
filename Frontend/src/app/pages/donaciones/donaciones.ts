import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { mensajeError } from '../../core/http/api-error';
import { estadoDonacionDto } from '../../core/mappers/donacion.mapper';
import { DonacionCreateDto } from '../../models/api/donacion.dto';
import { Donacion, EstadoDonacion } from '../../models/donacion';
import { Usuario } from '../../models/usuario';
import { DonacionService } from '../../services/donacion';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-donaciones',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './donaciones.html',
  styleUrl: './donaciones.css',
})
export class DonacionesComponent implements OnInit {
  private readonly donacionService = inject(DonacionService);
  private readonly usuarioService = inject(UsuarioService);

  readonly donaciones = this.donacionService.donaciones;
  readonly usuarioActual = this.usuarioService.usuarioActual;
  readonly esAdmin = computed(() =>
    this.usuarioService.esAdmin(this.usuarioService.usuarioActual()?.tipo),
  );
  readonly negocios = signal<Usuario[]>([]);
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly editandoId = signal<number | null>(null);
  readonly hoy = new Date().toISOString().split('T')[0];

  donacionForm = new FormGroup({
    nombreAlimento: new FormControl('', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]),
    descripcion: new FormControl('', [Validators.required, Validators.minLength(5), Validators.maxLength(500)]),
    cantidad: new FormControl(1, [Validators.required, Validators.min(1)]),
    unidadMedida: new FormControl('kg', Validators.required),
    fechaVencimiento: new FormControl('', Validators.required),
    direccionRecogida: new FormControl('', [Validators.required, Validators.minLength(5), Validators.maxLength(250)]),
    horarioDisponible: new FormControl('', [Validators.required, Validators.minLength(3), Validators.maxLength(100)]),
    usuarioNegocioId: new FormControl<number | null>(null),
  });

  ngOnInit(): void {
    this.cargarDonaciones();
    if (this.esAdmin()) {
      this.cargarNegocios();
    }
  }

  guardarDonacion(): void {
    this.mensaje.set('');
    this.error.set('');

    if (this.donacionForm.invalid) {
      this.donacionForm.markAllAsTouched();
      this.error.set('Complete todos los campos obligatorios.');
      return;
    }

    const usuario = this.usuarioActual();
    const negocioId = this.esAdmin()
      ? this.donacionForm.value.usuarioNegocioId
      : usuario?.id ?? null;

    if (!negocioId) {
      this.error.set('Seleccione el negocio donante.');
      return;
    }

    const campos = {
      nombre_alimento: this.donacionForm.value.nombreAlimento ?? '',
      descripcion: this.donacionForm.value.descripcion ?? '',
      cantidad: Number(this.donacionForm.value.cantidad ?? 0),
      unidad: this.donacionForm.value.unidadMedida ?? 'kg',
      fecha_vencimiento: this.donacionForm.value.fechaVencimiento ?? '',
      direccion_recojo: this.donacionForm.value.direccionRecogida ?? '',
      hora_disponible: this.donacionForm.value.horarioDisponible ?? '',
      usuario_negocio_id: Number(negocioId),
    };
    const datos: DonacionCreateDto = { ...campos, estado: 'disponible' };

    const edicion = this.editandoId();
    const peticion = edicion !== null
      ? this.donacionService.actualizar(edicion, campos)
      : this.donacionService.crear(datos);

    peticion.subscribe({
      next: () => {
        this.mensaje.set(
          edicion !== null
            ? 'Donación actualizada correctamente.'
            : 'Donación registrada correctamente.',
        );
        this.resetFormulario();
        this.cargarDonaciones();
      },
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  editarDonacion(donacion: Donacion): void {
    this.editandoId.set(donacion.id);
    this.donacionForm.patchValue({
      nombreAlimento: donacion.nombreAlimento,
      descripcion: donacion.descripcion,
      cantidad: donacion.cantidad,
      unidadMedida: donacion.unidadMedida,
      fechaVencimiento: donacion.fechaVencimiento,
      direccionRecogida: donacion.direccionRecogida,
      horarioDisponible: donacion.horarioDisponible,
      usuarioNegocioId: donacion.donanteId,
    });
  }

  cancelarDonacion(id: number): void {
    if (!window.confirm('¿Desea cancelar esta donación?')) {
      return;
    }

    this.mensaje.set('');
    this.error.set('');
    this.donacionService.eliminar(id).subscribe({
      next: () => this.mensaje.set('Donación cancelada.'),
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  cambiarEstado(id: number, estado: EstadoDonacion): void {
    this.mensaje.set('');
    this.error.set('');
    this.donacionService.cambiarEstado(id, estadoDonacionDto(estado)).subscribe({
      next: () => this.mensaje.set('Estado actualizado.'),
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  resetFormulario(): void {
    this.editandoId.set(null);
    this.donacionForm.reset({
      nombreAlimento: '',
      descripcion: '',
      cantidad: 1,
      unidadMedida: 'kg',
      fechaVencimiento: '',
      direccionRecogida: '',
      horarioDisponible: '',
      usuarioNegocioId: null,
    });
  }

  private cargarDonaciones(): void {
    this.donacionService.listar().subscribe({
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  private cargarNegocios(): void {
    this.usuarioService.listarUsuarios().subscribe({
      next: (usuarios) => this.negocios.set(usuarios.filter((usuario) => usuario.rol === 'negocio')),
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }
}
