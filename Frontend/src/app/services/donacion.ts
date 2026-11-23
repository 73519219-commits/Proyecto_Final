import { computed, inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable, tap } from 'rxjs';
import { API_BASE_URL } from '../core/api.config';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { toDonacion } from '../core/mappers/donacion.mapper';
import {
  DonacionCreateDto,
  DonacionDto,
  DonacionUpdateDto,
  EstadoDonacionDto,
} from '../models/api/donacion.dto';
import { Donacion } from '../models/donacion';

@Injectable({ providedIn: 'root' })
export class DonacionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly tokenStorage = inject(TokenStorageService);

  private readonly donacionesSignal = signal<Donacion[]>([]);

  readonly donaciones = this.donacionesSignal.asReadonly();
  readonly donacionesDisponibles = computed(() =>
    this.donaciones().filter((donacion) => donacion.estado === 'Disponible'),
  );

  constructor() {
    this.tokenStorage.sesionInvalidada$.subscribe(() => this.donacionesSignal.set([]));
  }

  listar(): Observable<Donacion[]> {
    return this.http.get<DonacionDto[]>(`${this.baseUrl}/donaciones/`).pipe(
      map((dtos) => dtos.map(toDonacion)),
      tap((donaciones) => this.donacionesSignal.set(donaciones)),
    );
  }

  listarDisponibles(): Observable<Donacion[]> {
    return this.http.get<DonacionDto[]>(`${this.baseUrl}/donaciones/disponibles`).pipe(
      map((dtos) => dtos.map(toDonacion)),
      tap((donaciones) => this.donacionesSignal.set(donaciones)),
    );
  }

  crear(datos: DonacionCreateDto): Observable<Donacion> {
    return this.http.post<DonacionDto>(`${this.baseUrl}/donaciones/`, datos).pipe(
      map((dto) => toDonacion(dto)),
      tap((donacion) => this.upsert(donacion)),
    );
  }

  actualizar(id: number, datos: DonacionUpdateDto): Observable<Donacion> {
    return this.http.put<DonacionDto>(`${this.baseUrl}/donaciones/${id}`, datos).pipe(
      map((dto) => toDonacion(dto)),
      tap((donacion) => this.upsert(donacion)),
    );
  }

  cambiarEstado(id: number, estado: EstadoDonacionDto): Observable<Donacion> {
    return this.actualizar(id, { estado });
  }

  eliminar(id: number): Observable<{ mensaje: string }> {
    return this.http.delete<{ mensaje: string }>(`${this.baseUrl}/donaciones/${id}`).pipe(
      tap(() =>
        this.donacionesSignal.update((lista) =>
          lista.map((donacion) =>
            donacion.id === id ? { ...donacion, estado: 'Cancelada' } : donacion,
          ),
        ),
      ),
    );
  }

  private upsert(donacion: Donacion): void {
    this.donacionesSignal.update((lista) =>
      lista.some((item) => item.id === donacion.id)
        ? lista.map((item) => (item.id === donacion.id ? donacion : item))
        : [donacion, ...lista],
    );
  }
}
