import { computed, inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable, tap } from 'rxjs';
import { API_BASE_URL } from '../core/api.config';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { toUsuario } from '../core/mappers/usuario.mapper';
import {
  LoginDto,
  LoginResponseDto,
  RegistroUsuarioDto,
  RolDto,
  UsuarioDto,
  UsuarioUpdateDto,
} from '../models/api/usuario.dto';
import { Usuario } from '../models/usuario';

const USUARIO_KEY = 'alimento_solidario_usuario';

@Injectable({ providedIn: 'root' })
export class UsuarioService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly tokenStorage = inject(TokenStorageService);

  private readonly usuariosSignal = signal<Usuario[]>([]);
  private readonly usuarioActualSignal = signal<Usuario | null>(this.leerUsuarioGuardado());

  readonly usuarioActual = this.usuarioActualSignal.asReadonly();
  readonly usuarios = this.usuariosSignal.asReadonly();
  readonly totalUsuarios = computed(() => this.usuarios().length);
  readonly usuariosActivos = computed(
    () => this.usuarios().filter((usuario) => usuario.estado === 'Activo').length,
  );

  constructor() {
    this.tokenStorage.sesionInvalidada$.subscribe(() => {
      this.usuariosSignal.set([]);
      this.usuarioActualSignal.set(null);
    });
  }

  login(correo: string, password: string): Observable<Usuario> {
    const cuerpo: LoginDto = { correo, password };

    return this.http.post<LoginResponseDto>(`${this.baseUrl}/auth/login`, cuerpo).pipe(
      map((respuesta) => {
        this.tokenStorage.guardar(respuesta.access_token);
        return toUsuario(respuesta.usuario);
      }),
      tap((usuario) => this.establecerUsuarioActual(usuario)),
    );
  }

  registrarUsuario(datos: RegistroUsuarioDto): Observable<Usuario> {
    return this.http
      .post<UsuarioDto>(`${this.baseUrl}/auth/registro`, datos)
      .pipe(map((dto) => toUsuario(dto)));
  }

  listarUsuarios(rol?: RolDto): Observable<Usuario[]> {
    return this.http.get<UsuarioDto[]>(`${this.baseUrl}/usuarios`, {
      params: rol ? { rol } : {},
    }).pipe(
      map((dtos) => dtos.map(toUsuario)),
      tap((usuarios) => this.usuariosSignal.set(usuarios)),
    );
  }

  actualizarUsuario(id: number, datos: UsuarioUpdateDto): Observable<Usuario> {
    return this.http.put<UsuarioDto>(`${this.baseUrl}/usuarios/${id}`, datos).pipe(
      map(toUsuario),
      tap((usuario) => this.upsertUsuario(usuario)),
    );
  }

  eliminarUsuario(id: number): Observable<{ mensaje: string }> {
    return this.http.delete<{ mensaje: string }>(`${this.baseUrl}/usuarios/${id}`).pipe(
      tap(() =>
        this.usuariosSignal.update((usuarios) =>
          usuarios.map((usuario) =>
            usuario.id === id ? { ...usuario, estado: 'Inactivo' } : usuario,
          ),
        ),
      ),
    );
  }

  cargarPerfil(): Observable<Usuario> {
    return this.http.get<UsuarioDto>(`${this.baseUrl}/usuarios/me`).pipe(
      map((dto) => toUsuario(dto)),
      tap((usuario) => this.establecerUsuarioActual(usuario)),
    );
  }

  actualizarDisponibilidad(disponible: boolean): Observable<Usuario> {
    return this.http
      .patch<UsuarioDto>(
        `${this.baseUrl}/usuarios/me/disponible`,
        null,
        { params: { disponible: String(disponible) } },
      )
      .pipe(
        map(toUsuario),
        tap((usuario) => this.establecerUsuarioActual(usuario)),
      );
  }

  esAdmin(tipo?: string): boolean {
    const tipoNormalizado = (tipo ?? '').trim().toLowerCase();
    return tipoNormalizado === 'admin' || tipoNormalizado === 'administrador';
  }

  esNegocio(tipo?: string): boolean {
    return (tipo ?? '').trim().toLowerCase() === 'negocio';
  }

  esComedor(tipo?: string): boolean {
    const tipoNormalizado = (tipo ?? '').trim().toLowerCase();
    return tipoNormalizado === 'comedor' || tipoNormalizado === 'comedor popular';
  }

  esVoluntario(tipo?: string): boolean {
    return (tipo ?? '').trim().toLowerCase() === 'voluntario';
  }

  cerrarSesion(): void {
    this.tokenStorage.limpiar();
    this.usuariosSignal.set([]);
    this.usuarioActualSignal.set(null);
    try {
      localStorage.removeItem(USUARIO_KEY);
    } catch {
      // Sin almacenamiento disponible.
    }
  }

  private establecerUsuarioActual(usuario: Usuario): void {
    this.usuarioActualSignal.set(usuario);
    try {
      localStorage.setItem(USUARIO_KEY, JSON.stringify(usuario));
    } catch {
      // La sesión queda solo en memoria.
    }
  }

  private upsertUsuario(usuario: Usuario): void {
    this.usuariosSignal.update((usuarios) =>
      usuarios.some((item) => item.id === usuario.id)
        ? usuarios.map((item) => (item.id === usuario.id ? usuario : item))
        : [usuario, ...usuarios],
    );
  }

  private leerUsuarioGuardado(): Usuario | null {
    try {
      const guardado = localStorage.getItem(USUARIO_KEY);
      return guardado ? (JSON.parse(guardado) as Usuario) : null;
    } catch {
      return null;
    }
  }
}
