import { computed, inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable, tap } from 'rxjs';
import { API_BASE_URL } from '../core/api.config';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { toSolicitud } from '../core/mappers/solicitud.mapper';
import {
  EstadoSolicitudDto,
  SolicitudCreateDto,
  SolicitudDto,
  SolicitudUpdateDto,
} from '../models/api/solicitud.dto';
import { Solicitud } from '../models/solicitud';

@Injectable({ providedIn: 'root' })
export class SolicitudService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly tokenStorage = inject(TokenStorageService);

  private readonly solicitudesSignal = signal<Solicitud[]>([]);

  readonly solicitudes = this.solicitudesSignal.asReadonly();
  readonly solicitudesPendientes = computed(
    () => this.solicitudes().filter((solicitud) => solicitud.estado === 'Pendiente').length,
  );

  constructor() {
    this.tokenStorage.sesionInvalidada$.subscribe(() => this.solicitudesSignal.set([]));
  }

  listar(): Observable<Solicitud[]> {
    return this.http.get<SolicitudDto[]>(`${this.baseUrl}/solicitudes/`).pipe(
      map((dtos) => dtos.map(toSolicitud)),
      tap((solicitudes) => this.solicitudesSignal.set(solicitudes)),
    );
  }

  crear(datos: SolicitudCreateDto): Observable<Solicitud> {
    return this.http.post<SolicitudDto>(`${this.baseUrl}/solicitudes/`, datos).pipe(
      map((dto) => toSolicitud(dto)),
      tap((solicitud) => this.upsert(solicitud)),
    );
  }

  actualizar(id: number, datos: SolicitudUpdateDto): Observable<Solicitud> {
    return this.http.put<SolicitudDto>(`${this.baseUrl}/solicitudes/${id}`, datos).pipe(
      map((dto) => toSolicitud(dto)),
      tap((solicitud) => this.upsert(solicitud)),
    );
  }

  cambiarEstado(id: number, estado: EstadoSolicitudDto): Observable<Solicitud> {
    return this.http
      .patch<SolicitudDto>(`${this.baseUrl}/solicitudes/${id}/estado`, { estado })
      .pipe(
        map((dto) => toSolicitud(dto)),
        tap((solicitud) => this.upsert(solicitud)),
      );
  }

  aprobar(id: number, tipoApoyo?: 'recoger' | 'trasladar' | 'ambos'): Observable<Solicitud> {
    return this.http
      .post<SolicitudDto>(`${this.baseUrl}/solicitudes/${id}/aprobar`, tipoApoyo ? { tipo_apoyo: tipoApoyo } : {})
      .pipe(
        map((dto) => toSolicitud(dto)),
        tap((solicitud) => this.upsert(solicitud)),
      );
  }

  rechazar(id: number): Observable<Solicitud> {
    return this.http
      .post<SolicitudDto>(`${this.baseUrl}/solicitudes/${id}/rechazar`, {})
      .pipe(
        map((dto) => toSolicitud(dto)),
        tap((solicitud) => this.upsert(solicitud)),
      );
  }

  eliminar(id: number): Observable<{ mensaje: string }> {
    return this.http.delete<{ mensaje: string }>(`${this.baseUrl}/solicitudes/${id}`).pipe(
      tap(() =>
        this.solicitudesSignal.update((lista) =>
          lista.map((solicitud) =>
            solicitud.id === id ? { ...solicitud, estado: 'Cancelada' } : solicitud,
          ),
        ),
      ),
    );
  }

  private upsert(solicitud: Solicitud): void {
    this.solicitudesSignal.update((lista) =>
      lista.some((item) => item.id === solicitud.id)
        ? lista.map((item) => (item.id === solicitud.id ? solicitud : item))
        : [solicitud, ...lista],
    );
  }
}
