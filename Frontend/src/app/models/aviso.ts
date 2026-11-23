export interface Aviso {
  id: number;
  usuarioDestino: number;
  tipo: string;
  mensaje: string;
  referenciaId: number | null;
  leido: boolean;
  createdAt: string;
}
