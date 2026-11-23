export type EstadoSolicitudDto = 'pendiente' | 'aprobada' | 'rechazada' | 'cancelada';
export type TipoApoyoDto = 'recoger' | 'trasladar' | 'ambos';

/** Contrato exacto devuelto por `SolicitudOut` de FastAPI. */
export interface SolicitudDto {
  id: number;
  donacion_id: number;
  comedor_id: number;
  cantidad_solicitada: number;
  estado: EstadoSolicitudDto;
  tipo_apoyo: TipoApoyoDto;
  necesita_apoyo: TipoApoyoDto;
  telefono_negocio?: string | null;
  telefono_comedor?: string | null;
}

/** Cuerpo de `POST /api/solicitudes/`. */
export interface SolicitudCreateDto {
  donacion_id: number;
  comedor_id: number;
  cantidad_solicitada: number;
  estado?: 'pendiente';
  tipo_apoyo?: TipoApoyoDto;
  necesita_apoyo?: TipoApoyoDto;
}

/** Cuerpo de `PUT /api/solicitudes/{id}`. */
export type SolicitudUpdateDto = Partial<SolicitudCreateDto>;
