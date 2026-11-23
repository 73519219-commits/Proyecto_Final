export interface AvisoDto {
  id: number;
  usuario_destino: number;
  tipo: string;
  mensaje: string;
  referencia_id: number | null;
  leido: boolean;
  created_at: string;
}
