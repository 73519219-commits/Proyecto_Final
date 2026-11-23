import { EntregaDto, EstadoEntregaDto } from '../../models/api/entrega.dto';
import { Entrega, EstadoEntrega } from '../../models/voluntario';

const ESTADO_UI: Record<EstadoEntregaDto, EstadoEntrega> = {
  abierta: 'Abierta',
  aceptada: 'Aceptada',
  recogida: 'Recogida',
  entregada: 'Entregada',
  cancelada: 'Cancelada',
};

const ESTADO_DTO: Record<EstadoEntrega, EstadoEntregaDto> = {
  Abierta: 'abierta',
  Aceptada: 'aceptada',
  Recogida: 'recogida',
  Entregada: 'entregada',
  Cancelada: 'cancelada',
};

export function estadoEntregaDto(estado: EstadoEntrega): EstadoEntregaDto {
  return ESTADO_DTO[estado];
}

export function toEntrega(dto: EntregaDto): Entrega {
  return {
    id: dto.id,
    solicitudId: dto.solicitud_id,
    voluntarioId: dto.voluntario_id,
    fechaAsignacion: dto.fecha_asignacion,
    fechaEntrega: dto.fecha_entrega,
    estado: ESTADO_UI[dto.estado] ?? 'Abierta',
    observaciones: dto.observaciones,
    tipoApoyo: dto.tipo_apoyo,
    telefonoNegocio: dto.telefono_negocio,
    telefonoComedor: dto.telefono_comedor,
    direccionRecojo: dto.direccion_recojo,
    cantidad: dto.cantidad,
    unidad: dto.unidad,
    horarioDisponible: dto.hora_disponible,
  };
}
