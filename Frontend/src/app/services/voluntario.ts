import { computed, inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable, tap } from 'rxjs';
import { API_BASE_URL } from '../core/api.config';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { toEntrega } from '../core/mappers/entrega.mapper';
import { EntregaDto, EstadoEntregaDto } from '../models/api/entrega.dto';
import { Entrega } from '../models/voluntario';

@Injectable({ providedIn: 'root' })
export class VoluntarioService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly tokenStorage = inject(TokenStorageService);

  private readonly abiertasSignal = signal<Entrega[]>([]);
  private readonly asignadasSignal = signal<Entrega[]>([]);

  constructor() {
    this.tokenStorage.sesionInvalidada$.subscribe(() => {
      this.abiertasSignal.set([]);
      this.asignadasSignal.set([]);
    });
  }

  readonly entregas = computed(() => {
    const entregasPorId = new Map<number, Entrega>();
    for (const entrega of this.abiertasSignal()) {
      entregasPorId.set(entrega.id, entrega);
    }
    for (const entrega of this.asignadasSignal()) {
      entregasPorId.set(entrega.id, entrega);
    }
    return [...entregasPorId.values()];
  });
  readonly entregasPendientes = computed(
    () => this.entregas().filter((entrega) => entrega.estado === 'Abierta').length,
  );

  listarEntregas(): Observable<Entrega[]> {
    return this.http.get<EntregaDto[]>(`${this.baseUrl}/voluntarios/entregas`).pipe(
      map((dtos) => dtos.map(toEntrega)),
      tap((entregas) => this.asignadasSignal.set(entregas)),
    );
  }

  aceptarEntrega(id: number): Observable<Entrega> {
    return this.http
      .post<EntregaDto>(`${this.baseUrl}/voluntarios/entregas/${id}/aceptar`, {})
      .pipe(
        map((dto) => toEntrega(dto)),
        tap((entrega) => this.upsertAsignada(entrega)),
      );
  }

  listarAbiertas(): Observable<Entrega[]> {
    return this.http.get<EntregaDto[]>(`${this.baseUrl}/voluntarios/entregas/abiertas`).pipe(
      map((dtos) => dtos.map(toEntrega)),
      tap((entregas) => this.abiertasSignal.set(entregas)),
    );
  }

  pasarEntrega(id: number): Observable<{ mensaje: string }> {
    return this.http.post<{ mensaje: string }>(
      `${this.baseUrl}/voluntarios/entregas/${id}/pasar`,
      {},
    ).pipe(
      tap(() => this.abiertasSignal.update((lista) => lista.filter((entrega) => entrega.id !== id))),
    );
  }

  cambiarEstadoEntrega(id: number, estado: EstadoEntregaDto): Observable<Entrega> {
    return this.http
      .patch<EntregaDto>(`${this.baseUrl}/voluntarios/entregas/${id}/estado`, { estado })
      .pipe(
        map((dto) => toEntrega(dto)),
        tap((entrega) => this.upsertEntrega(entrega)),
      );
  }

  marcarRecogido(id: number): Observable<Entrega> {
    return this.http
      .post<EntregaDto>(`${this.baseUrl}/voluntarios/entregas/${id}/recogido`, {})
      .pipe(
        map((dto) => toEntrega(dto)),
        tap((entrega) => this.upsertEntrega(entrega)),
      );
  }

  confirmarEntrega(id: number): Observable<Entrega> {
    return this.http
      .post<EntregaDto>(`${this.baseUrl}/voluntarios/entregas/${id}/confirmar`, {})
      .pipe(
        map((dto) => toEntrega(dto)),
        tap((entrega) => this.upsertEntrega(entrega)),
      );
  }

  private upsertAsignada(entrega: Entrega): void {
    this.abiertasSignal.update((lista) =>
      lista.filter((item) => item.id !== entrega.id),
    );
    this.asignadasSignal.update((lista) =>
      lista.some((item) => item.id === entrega.id)
        ? lista.map((item) => (item.id === entrega.id ? entrega : item))
        : [entrega, ...lista],
    );
  }

  private upsertEntrega(entrega: Entrega): void {
    if (entrega.estado === 'Abierta') {
      this.asignadasSignal.update((lista) =>
        lista.filter((item) => item.id !== entrega.id),
      );
      this.abiertasSignal.update((lista) =>
        lista.some((item) => item.id === entrega.id)
          ? lista.map((item) => (item.id === entrega.id ? entrega : item))
          : [entrega, ...lista],
      );
      return;
    }
    this.upsertAsignada(entrega);
  }
}
