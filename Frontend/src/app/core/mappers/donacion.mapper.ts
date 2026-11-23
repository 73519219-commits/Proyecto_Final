import { DonacionDto, EstadoDonacionDto } from '../../models/api/donacion.dto';
import { Donacion, EstadoDonacion } from '../../models/donacion';

const ESTADO_UI: Record<EstadoDonacionDto, EstadoDonacion> = {
  disponible: 'Disponible',
  reservada: 'Reservada',
  cancelada: 'Cancelada',
  entregada: 'Entregada',
};

const ESTADO_DTO: Record<EstadoDonacion, EstadoDonacionDto> = {
  Disponible: 'disponible',
  Reservada: 'reservada',
  Cancelada: 'cancelada',
  Entregada: 'entregada',
};

export function estadoDonacionDto(estado: EstadoDonacion): EstadoDonacionDto {
  return ESTADO_DTO[estado];
}

export function toDonacion(dto: DonacionDto): Donacion {
  return {
    id: dto.id,
    nombreAlimento: dto.nombre_alimento,
    descripcion: dto.descripcion,
    cantidad: dto.cantidad,
    unidadMedida: dto.unidad,
    fechaVencimiento: dto.fecha_vencimiento,
    direccionRecogida: dto.direccion_recojo,
    horarioDisponible: dto.hora_disponible,
    estado: ESTADO_UI[dto.estado] ?? 'Disponible',
    donanteId: dto.usuario_negocio_id,
  };
}
