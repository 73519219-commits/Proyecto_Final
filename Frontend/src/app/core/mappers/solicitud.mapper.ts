import { EstadoSolicitudDto, SolicitudDto } from '../../models/api/solicitud.dto';
import { EstadoSolicitud, Solicitud } from '../../models/solicitud';

const ESTADO_UI: Record<EstadoSolicitudDto, EstadoSolicitud> = {
  pendiente: 'Pendiente',
  aprobada: 'Aprobada',
  rechazada: 'Rechazada',
  cancelada: 'Cancelada',
};

const ESTADO_DTO: Record<EstadoSolicitud, EstadoSolicitudDto> = {
  Pendiente: 'pendiente',
  Aprobada: 'aprobada',
  Rechazada: 'rechazada',
  Cancelada: 'cancelada',
};

export function estadoSolicitudDto(estado: EstadoSolicitud): EstadoSolicitudDto {
  return ESTADO_DTO[estado];
}

export function toSolicitud(dto: SolicitudDto): Solicitud {
  return {
    id: dto.id,
    donacionId: dto.donacion_id,
    comedorId: dto.comedor_id,
    cantidadSolicitada: dto.cantidad_solicitada,
    estado: ESTADO_UI[dto.estado] ?? 'Pendiente',
    tipoApoyo: dto.tipo_apoyo,
    necesitaApoyo: dto.necesita_apoyo,
    telefonoNegocio: dto.telefono_negocio,
    telefonoComedor: dto.telefono_comedor,
  };
}
