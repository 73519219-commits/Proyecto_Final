export type EstadoDonacionDto = 'disponible' | 'reservada' | 'cancelada' | 'entregada';

/** Contrato exacto devuelto por `DonacionOut` de FastAPI. */
export interface DonacionDto {
  id: number;
  nombre_alimento: string;
  descripcion: string;
  cantidad: number;
  unidad: string;
  fecha_vencimiento: string;
  direccion_recojo: string;
  hora_disponible: string;
  estado: EstadoDonacionDto;
  usuario_negocio_id: number;
}

/** Cuerpo de `POST /api/donaciones/`. */
export interface DonacionCreateDto {
  nombre_alimento: string;
  descripcion: string;
  cantidad: number;
  unidad: string;
  fecha_vencimiento: string;
  direccion_recojo: string;
  hora_disponible: string;
  estado: EstadoDonacionDto;
  usuario_negocio_id: number;
}

/** Cuerpo de `PUT /api/donaciones/{id}` (todos los campos son opcionales). */
export type DonacionUpdateDto = Partial<DonacionCreateDto>;
