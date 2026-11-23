export type RolDto = 'admin' | 'negocio' | 'comedor' | 'voluntario';
export type EstadoUsuarioDto = 'activo' | 'inactivo';

/** Contrato exacto devuelto por `UsuarioOut` de FastAPI. */
export interface UsuarioDto {
  id: number;
  nombres: string;
  apellidos: string;
  correo: string;
  telefono: string;
  direccion: string;
  rol: RolDto;
  disponible?: boolean;
  estado: EstadoUsuarioDto;
}

/** Cuerpo de `POST /api/auth/login`. */
export interface LoginDto {
  correo: string;
  password: string;
}

/** Respuesta de `POST /api/auth/login`. */
export interface LoginResponseDto {
  access_token: string;
  token_type: string;
  usuario: UsuarioDto;
}

/** Cuerpo de `POST /api/auth/registro`. */
export interface RegistroUsuarioDto {
  nombres: string;
  apellidos: string;
  correo: string;
  password: string;
  telefono: string;
  direccion: string;
  rol: RolDto;
  disponible?: boolean;
  estado?: EstadoUsuarioDto;
}

export type UsuarioUpdateDto = Partial<Omit<RegistroUsuarioDto, 'password'>> & {
  password?: string;
};
