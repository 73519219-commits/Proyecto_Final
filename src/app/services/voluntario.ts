import { computed, Injectable, signal } from '@angular/core';
import { Entrega, Voluntario } from '../models/voluntario';

@Injectable({ providedIn: 'root' })
export class VoluntarioService {
  private readonly voluntariosSignal = signal<Voluntario[]>([
    {
      id: 1,
      nombre: 'Pedro Álvarez',
      email: 'pedro@correo.pe',
      telefono: '951234567',
      zona: 'Centro',
      disponibilidad: 'Mañana y tarde',
      estado: 'Disponible',
    },
    {
      id: 2,
      nombre: 'María Torres',
      email: 'maria@correo.pe',
      telefono: '942345678',
      zona: 'San Isidro',
      disponibilidad: 'Tarde',
      estado: 'Ocupado',
    }
  ]);

  private readonly entregasSignal = signal<Entrega[]>([
    {
      id: 1,
      donacionId: 1,
      voluntarioId: 1,
      direccion: 'Av. El Sol 654',
      horario: '08:00 - 09:30',
      estado: 'Pendiente',
    },
    {
      id: 2,
      donacionId: 2,
      voluntarioId: 2,
      direccion: 'Jr. Cuzco 101',
      horario: '10:00 - 11:30',
      estado: 'En tránsito',
    }
  ]);

  readonly voluntarios = this.voluntariosSignal.asReadonly();
  readonly entregas = this.entregasSignal.asReadonly();
  readonly entregasPendientes = computed(() =>
    this.entregas().filter((entrega) => entrega.estado === 'Pendiente').length,
  );

  registrarVoluntario(voluntario: Voluntario): Voluntario {
    const nuevoVoluntario = { ...voluntario, id: Date.now() };
    this.voluntariosSignal.update((lista) => [nuevoVoluntario, ...lista]);
    return nuevoVoluntario;
  }

  registrarEntrega(entrega: Entrega): Entrega {
    const nuevaEntrega = { ...entrega, id: Date.now() };
    this.entregasSignal.update((lista) => [nuevaEntrega, ...lista]);
    return nuevaEntrega;
  }

  aceptarEntrega(id: number): void {
    this.entregasSignal.update((lista) =>
      lista.map((entrega) =>
        entrega.id === id ? { ...entrega, estado: 'En tránsito' } : entrega,
      ),
    );
  }

  cambiarEstadoEntrega(id: number, estado: Entrega['estado']): void {
    this.entregasSignal.update((lista) =>
      lista.map((entrega) =>
        entrega.id === id ? { ...entrega, estado } : entrega,
      ),
    );
  }
}
