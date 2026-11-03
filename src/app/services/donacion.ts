import { computed, Injectable, signal } from '@angular/core';
import { Donacion } from '../models/donacion';

@Injectable({ providedIn: 'root' })
export class DonacionService {
  private readonly donacionesSignal = signal<Donacion[]>([
    {
      id: 1,
      nombreAlimento: 'Pan de trigo',
      descripcion: 'Pan recién horneado, listo para entregar.',
      cantidad: 30,
      unidadMedida: 'unidad',
      fechaVencimiento: '2026-11-05',
      direccionRecogida: 'Av. El Sol 654',
      horarioDisponible: '08:00 - 11:00',
      estado: 'Disponible',
      donanteId: 2,
    },
    {
      id: 2,
      nombreAlimento: 'Arroz',
      descripcion: 'Sacos de arroz en buen estado.',
      cantidad: 25,
      unidadMedida: 'kg',
      fechaVencimiento: '2026-12-20',
      direccionRecogida: 'Jr. Cuzco 101',
      horarioDisponible: '09:00 - 13:00',
      estado: 'Reservada',
      donanteId: 2,
    },
    {
      id: 3,
      nombreAlimento: 'Frutas',
      descripcion: 'Caja de manzanas y peras frescas.',
      cantidad: 18,
      unidadMedida: 'kg',
      fechaVencimiento: '2026-11-04',
      direccionRecogida: 'Mercado Central',
      horarioDisponible: '10:00 - 12:00',
      estado: 'Disponible',
      donanteId: 2,
    }
  ]);

  readonly donaciones = this.donacionesSignal.asReadonly();
  readonly donacionesDisponibles = computed(() =>
    this.donaciones().filter((donacion) => donacion.estado === 'Disponible'),
  );

  registrarDonacion(donacion: Donacion): Donacion {
    const nuevaDonacion = { ...donacion, id: Date.now() };
    this.donacionesSignal.update((lista) => [nuevaDonacion, ...lista]);
    return nuevaDonacion;
  }

  actualizarDonacion(id: number, donacionActualizada: Donacion): void {
    this.donacionesSignal.update((lista) =>
      lista.map((donacion) => (donacion.id === id ? { ...donacion, ...donacionActualizada } : donacion)),
    );
  }

  eliminarDonacion(id: number): void {
    this.donacionesSignal.update((lista) => lista.filter((donacion) => donacion.id !== id));
  }

  cambiarEstado(id: number, estado: Donacion['estado']): void {
    this.donacionesSignal.update((lista) =>
      lista.map((donacion) =>
        donacion.id === id ? { ...donacion, estado } : donacion,
      ),
    );
  }
}
