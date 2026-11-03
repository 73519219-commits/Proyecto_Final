export type EstadoEntrega = 'Pendiente' | 'En tránsito' | 'Entregada' | 'Cancelada';

export interface Voluntario {
  id: number;
  nombre: string;
  email: string;
  telefono: string;
  zona: string;
  disponibilidad: string;
  estado: 'Disponible' | 'Ocupado';
}

export interface Entrega {
  id: number;
  donacionId: number;
  voluntarioId: number;
  direccion: string;
  horario: string;
  estado: EstadoEntrega;
}
