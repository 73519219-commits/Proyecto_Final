import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { Donacion, EstadoDonacion } from '../../models/donacion';
import { DonacionService } from '../../services/donacion';

@Component({
  selector: 'app-donaciones',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './donaciones.html',
  styleUrl: './donaciones.css',
})
export class DonacionesComponent {
  private readonly donacionService = inject(DonacionService);
  readonly donaciones = this.donacionService.donaciones;
  readonly mensaje = signal('');
  readonly editandoId = signal<number | null>(null);

  donacionForm = new FormGroup({
    nombreAlimento: new FormControl('', Validators.required),
    descripcion: new FormControl('', Validators.required),
    cantidad: new FormControl(1, [Validators.required, Validators.min(1)]),
    unidadMedida: new FormControl('kg', Validators.required),
    fechaVencimiento: new FormControl('', Validators.required),
    direccionRecogida: new FormControl('', Validators.required),
    horarioDisponible: new FormControl('', Validators.required),
    estado: new FormControl<EstadoDonacion>('Disponible', Validators.required),
  });

  guardarDonacion(): void {
    if (this.donacionForm.invalid) {
      this.donacionForm.markAllAsTouched();
      this.mensaje.set('Complete todos los campos obligatorios.');
      return;
    }

    const data: Donacion = {
      id: this.editandoId() ?? Date.now(),
      nombreAlimento: this.donacionForm.value.nombreAlimento ?? '',
      descripcion: this.donacionForm.value.descripcion ?? '',
      cantidad: Number(this.donacionForm.value.cantidad ?? 0),
      unidadMedida: this.donacionForm.value.unidadMedida ?? 'kg',
      fechaVencimiento: this.donacionForm.value.fechaVencimiento ?? '',
      direccionRecogida: this.donacionForm.value.direccionRecogida ?? '',
      horarioDisponible: this.donacionForm.value.horarioDisponible ?? '',
      estado: (this.donacionForm.value.estado as EstadoDonacion) ?? 'Disponible',
      donanteId: 2,
    };

    if (this.editandoId() !== null) {
      this.donacionService.actualizarDonacion(this.editandoId()!, data);
      this.mensaje.set('Donación actualizada correctamente.');
    } else {
      this.donacionService.registrarDonacion(data);
      this.mensaje.set('Donación registrada correctamente.');
    }

    this.resetFormulario();
  }

  editarDonacion(donacion: Donacion): void {
    this.editandoId.set(donacion.id);
    this.donacionForm.patchValue(donacion);
  }

  eliminarDonacion(id: number): void {
    this.donacionService.eliminarDonacion(id);
    this.mensaje.set('Donación eliminada.');
  }

  cambiarEstado(id: number, estado: EstadoDonacion): void {
    this.donacionService.cambiarEstado(id, estado);
    this.mensaje.set('Estado actualizado.');
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
      estado: 'Disponible',
    });
  }
}
