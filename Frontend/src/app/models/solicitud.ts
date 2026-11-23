export type EstadoSolicitud = 'Pendiente' | 'Aprobada' | 'Rechazada' | 'Cancelada';

/** Modelo de presentación usado por componentes y templates. */
export interface Solicitud {
  id: number;
  donacionId: number;
  comedorId: number;
  cantidadSolicitada: number;
  estado: EstadoSolicitud;
  tipoApoyo: 'recoger' | 'trasladar' | 'ambos';
  necesitaApoyo: 'recoger' | 'trasladar' | 'ambos';
  telefonoNegocio?: string | null;
  telefonoComedor?: string | null;
}
