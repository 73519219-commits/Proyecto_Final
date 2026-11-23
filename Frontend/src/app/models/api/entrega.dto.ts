export type EstadoEntregaDto =
  | 'abierta'
  | 'aceptada'
  | 'recogida'
  | 'entregada'
  | 'cancelada';
export type TipoApoyoDto = 'recoger' | 'trasladar' | 'ambos';

/** Contrato exacto devuelto por `EntregaOut` de FastAPI. */
export interface EntregaDto {
  id: number;
  solicitud_id: number;
  voluntario_id: number;
  fecha_asignacion: string;
  fecha_entrega: string | null;
  estado: EstadoEntregaDto;
  observaciones: string | null;
  tipo_apoyo: TipoApoyoDto;
  telefono_negocio?: string | null;
  telefono_comedor?: string | null;
  direccion_recojo?: string | null;
  cantidad?: number | null;
  unidad?: string | null;
  hora_disponible?: string | null;
}
