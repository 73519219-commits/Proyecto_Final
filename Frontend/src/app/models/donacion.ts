export type EstadoDonacion = 'Disponible' | 'Reservada' | 'Cancelada' | 'Entregada';

/** Modelo de presentación usado por componentes y templates. */
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
