import { RolDto } from './api/usuario.dto';

export type Rol = RolDto;
export type TipoUsuario = 'Administrador' | 'Negocio' | 'Comedor popular' | 'Voluntario';

/** Modelo de presentación usado por componentes y templates. */
export interface Usuario {
  id: number;
  nombres: string;
  apellidos: string;
  /** Nombre completo derivado de `nombres` + `apellidos`. */
  nombre: string;
  email: string;
  rol: Rol;
  /** Etiqueta visible del rol. */
  tipo: TipoUsuario;
  telefono: string;
  direccion: string;
  estado: 'Activo' | 'Inactivo';
  disponible: boolean;
}
