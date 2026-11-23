export type EstadoEntrega =
  | 'Abierta'
  | 'Aceptada'
  | 'Recogida'
  | 'Entregada'
  | 'Cancelada';

/** Modelo de presentación usado por componentes y templates. */
export interface Entrega {
  id: number;
  solicitudId: number;
  voluntarioId: number;
  fechaAsignacion: string;
  fechaEntrega: string | null;
  estado: EstadoEntrega;
  observaciones: string | null;
  tipoApoyo: 'recoger' | 'trasladar' | 'ambos';
  telefonoNegocio?: string | null;
  telefonoComedor?: string | null;
  direccionRecojo?: string | null;
  cantidad?: number | null;
  unidad?: string | null;
  horarioDisponible?: string | null;
}
