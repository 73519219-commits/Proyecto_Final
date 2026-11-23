import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map, Observable, tap } from 'rxjs';
import { API_BASE_URL } from '../core/api.config';
import { TokenStorageService } from '../core/auth/token-storage.service';
import { AvisoDto } from '../models/api/aviso.dto';
import { Aviso } from '../models/aviso';

@Injectable({ providedIn: 'root' })
export class AvisoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);
  private readonly tokenStorage = inject(TokenStorageService);
  private readonly avisosSignal = signal<Aviso[]>([]);

  readonly avisos = this.avisosSignal.asReadonly();

  constructor() {
    this.tokenStorage.sesionInvalidada$.subscribe(() => this.limpiar());
  }

  listar(): Observable<Aviso[]> {
    return this.http.get<AvisoDto[]>(`${this.baseUrl}/avisos/`).pipe(
      map((dtos) => dtos.map((dto) => ({
        id: dto.id,
        usuarioDestino: dto.usuario_destino,
        tipo: dto.tipo,
        mensaje: dto.mensaje,
        referenciaId: dto.referencia_id,
        leido: dto.leido,
        createdAt: dto.created_at,
      }))),
      tap((avisos) => this.avisosSignal.set(avisos)),
    );
  }

  marcarLeido(id: number): Observable<Aviso> {
    return this.http.patch<AvisoDto>(`${this.baseUrl}/avisos/${id}/leer`, {}).pipe(
      map((dto) => ({
        id: dto.id,
        usuarioDestino: dto.usuario_destino,
        tipo: dto.tipo,
        mensaje: dto.mensaje,
        referenciaId: dto.referencia_id,
        leido: dto.leido,
        createdAt: dto.created_at,
      })),
      tap((aviso) => this.avisosSignal.update((lista) =>
        lista.map((item) => item.id === aviso.id ? aviso : item),
      )),
    );
  }

  limpiar(): void {
    this.avisosSignal.set([]);
  }
}
