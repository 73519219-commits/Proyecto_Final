import { computed, Injectable, signal } from '@angular/core';
import { Usuario } from '../models/usuario';

@Injectable({ providedIn: 'root' })
export class UsuarioService {
  private readonly usuariosSignal = signal<Usuario[]>([
    {
      id: 1,
      nombre: 'Administrador del sistema',
      email: 'admin@alimentosolidario.pe',
      password: 'admin123',
      tipo: 'Administrador',
      telefono: '987654321',
      direccion: 'Jr. Puno 115',
      estado: 'Activo',
    },
    {
      id: 2,
      nombre: 'Panadería San José',
      email: 'negocio@panaderia.pe',
      password: '123456',
      tipo: 'Negocio',
      telefono: '961234567',
      direccion: 'Av. Real 300',
      empresa: 'Panadería San José',
      estado: 'Activo',
    },
    {
      id: 3,
      nombre: 'Comedor popular Esperanza',
      email: 'comedor@esperanza.pe',
      password: '123456',
      tipo: 'Comedor popular',
      telefono: '991122334',
      direccion: 'Jr. Progreso 80',
      empresa: 'Comedor Esperanza',
      estado: 'Activo',
    },
    {
      id: 4,
      nombre: 'Carlos Ruiz',
      email: 'voluntario@correo.pe',
      password: '123456',
      tipo: 'Voluntario',
      telefono: '965432100',
      direccion: 'Urbanización San Martín',
      estado: 'Activo',
    }
  ]);

  readonly usuarioActual = signal<Usuario | null>(null);
  readonly usuarios = this.usuariosSignal.asReadonly();
  readonly totalUsuarios = computed(() => this.usuarios().length);
  readonly usuariosActivos = computed(() => this.usuarios().filter((usuario) => usuario.estado === 'Activo').length);

  esAdmin(tipo?: string): boolean {
    const tipoNormalizado = (tipo ?? '').trim().toLowerCase();
    return tipoNormalizado === 'admin' || tipoNormalizado === 'administrador';
  }

  esNegocio(tipo?: string): boolean {
    return (tipo ?? '').trim().toLowerCase() === 'negocio';
  }

  esComedor(tipo?: string): boolean {
    return (tipo ?? '').trim().toLowerCase() === 'comedor popular';
  }

  esVoluntario(tipo?: string): boolean {
    return (tipo ?? '').trim().toLowerCase() === 'voluntario';
  }

  loginSimulado(email: string, password: string): Usuario | null {
    const usuario = this.usuarios().find(
      (item) => item.email.toLowerCase() === email.toLowerCase() && item.password === password,
    );

    if (usuario) {
      this.usuarioActual.set(usuario);
      return usuario;
    }

    return null;
  }

  registrarUsuario(usuario: Usuario): Usuario {
    const nuevoUsuario = { ...usuario, id: Date.now() };
    this.usuariosSignal.update((lista) => [...lista, nuevoUsuario]);
    this.usuarioActual.set(nuevoUsuario);
    return nuevoUsuario;
  }

  actualizarUsuario(id: number, usuarioActualizado: Usuario): void {
    this.usuariosSignal.update((lista) =>
      lista.map((usuario) => (usuario.id === id ? { ...usuario, ...usuarioActualizado } : usuario)),
    );
  }

  eliminarUsuario(id: number): void {
    this.usuariosSignal.update((lista) => lista.filter((usuario) => usuario.id !== id));
    const usuarioActual = this.usuarioActual();
    if (usuarioActual?.id === id) {
      this.usuarioActual.set(null);
    }
  }

  cerrarSesion(): void {
    this.usuarioActual.set(null);
  }
}
