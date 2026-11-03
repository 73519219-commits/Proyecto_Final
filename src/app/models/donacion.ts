export type EstadoDonacion = 'Disponible' | 'Reservada' | 'Recogida' | 'Cancelada';

export interface Donacion {
  id: number;
  nombreAlimento: string;
  descripcion: string;
  cantidad: number;
  unidadMedida: string;
  fechaVencimiento: string;
  direccionRecogida: string;
  horarioDisponible: string;
  estado: EstadoDonacion;
  donanteId: number;
}
