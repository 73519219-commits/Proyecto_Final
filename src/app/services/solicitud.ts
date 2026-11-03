import { computed, Injectable, signal } from '@angular/core';
import { Solicitud } from '../models/solicitud';

@Injectable({ providedIn: 'root' })
export class SolicitudService {
  private readonly solicitudesSignal = signal<Solicitud[]>([
    {
      id: 1,
      donacionId: 1,
      comedorId: 3,
      comedorNombre: 'Comedor Esperanza',
      cantidadSolicitada: 12,
      fechaSolicitud: '2026-10-30',
      estado: 'Pendiente',
    },
    {
      id: 2,
      donacionId: 2,
      comedorId: 3,
      comedorNombre: 'Comedor Esperanza',
      cantidadSolicitada: 8,
      fechaSolicitud: '2026-10-31',
      estado: 'Aprobada',
    }
  ]);

  readonly solicitudes = this.solicitudesSignal.asReadonly();
  readonly solicitudesPendientes = computed(() =>
    this.solicitudes().filter((solicitud) => solicitud.estado === 'Pendiente').length,
  );

  registrarSolicitud(solicitud: Solicitud): Solicitud {
    const nuevaSolicitud = { ...solicitud, id: Date.now() };
    this.solicitudesSignal.update((lista) => [nuevaSolicitud, ...lista]);
    return nuevaSolicitud;
  }

  actualizarEstado(id: number, estado: Solicitud['estado']): void {
    this.solicitudesSignal.update((lista) =>
      lista.map((solicitud) =>
        solicitud.id === id ? { ...solicitud, estado } : solicitud,
      ),
    );
  }

  cancelarSolicitud(id: number): void {
    this.actualizarEstado(id, 'Cancelada');
  }
}
