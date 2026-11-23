import { rolDesdeTipo, toUsuario } from './usuario.mapper';

describe('usuario.mapper', () => {
  it('convierte el DTO snake_case al modelo de presentación', () => {
    const usuario = toUsuario({
      id: 7,
      nombres: 'Ana',
      apellidos: 'Quispe',
      correo: 'ana@correo.pe',
      telefono: '987654321',
      direccion: 'Jr. Puno 120',
      rol: 'comedor',
      estado: 'activo',
    });

    expect(usuario.nombre).toBe('Ana Quispe');
    expect(usuario.email).toBe('ana@correo.pe');
    expect(usuario.tipo).toBe('Comedor popular');
    expect(usuario.rol).toBe('comedor');
    expect(usuario.estado).toBe('Activo');
  });

  it('traduce las etiquetas de tipo al rol del backend', () => {
    expect(rolDesdeTipo('Administrador')).toBe('admin');
    expect(rolDesdeTipo('Negocio')).toBe('negocio');
    expect(rolDesdeTipo('Comedor popular')).toBe('comedor');
    expect(rolDesdeTipo('Voluntario')).toBe('voluntario');
  });
});
