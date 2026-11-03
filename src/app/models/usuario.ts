export type TipoUsuario = 'Administrador' | 'Negocio' | 'Comedor popular' | 'Voluntario';

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  password: string;
  tipo: TipoUsuario;
  telefono: string;
  direccion: string;
  empresa?: string;
  estado: 'Activo' | 'Inactivo';
}
