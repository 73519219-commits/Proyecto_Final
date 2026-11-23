import { RolDto, UsuarioDto } from '../../models/api/usuario.dto';
import { Rol, TipoUsuario, Usuario } from '../../models/usuario';

const TIPO_POR_ROL: Record<RolDto, TipoUsuario> = {
  admin: 'Administrador',
  negocio: 'Negocio',
  comedor: 'Comedor popular',
  voluntario: 'Voluntario',
};

const ROL_POR_TIPO: Record<TipoUsuario, RolDto> = {
  Administrador: 'admin',
  Negocio: 'negocio',
  'Comedor popular': 'comedor',
  Voluntario: 'voluntario',
};

export function tipoDesdeRol(rol: RolDto): TipoUsuario {
  return TIPO_POR_ROL[rol] ?? 'Voluntario';
}

export function rolDesdeTipo(tipo: string): Rol {
  return ROL_POR_TIPO[tipo as TipoUsuario] ?? 'negocio';
}

export function toUsuario(dto: UsuarioDto): Usuario {
  return {
    id: dto.id,
    nombres: dto.nombres,
    apellidos: dto.apellidos,
    nombre: `${dto.nombres} ${dto.apellidos}`.trim(),
    email: dto.correo,
    rol: dto.rol,
    tipo: tipoDesdeRol(dto.rol),
    telefono: dto.telefono,
    direccion: dto.direccion,
    estado: dto.estado === 'activo' ? 'Activo' : 'Inactivo',
    disponible: dto.disponible ?? false,
  };
}
