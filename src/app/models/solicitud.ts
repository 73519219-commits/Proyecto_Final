export type EstadoSolicitud = 'Pendiente' | 'Aprobada' | 'Cancelada' | 'Entregada';

export interface Solicitud {
  id: number;
  donacionId: number;
  comedorId: number;
  comedorNombre: string;
  cantidadSolicitada: number;
  fechaSolicitud: string;
  estado: EstadoSolicitud;
}
