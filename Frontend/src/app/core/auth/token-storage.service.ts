import { Injectable, signal } from '@angular/core';
import { Subject } from 'rxjs';

const TOKEN_KEY = 'alimento_solidario_token';
const USUARIO_KEY = 'alimento_solidario_usuario';

@Injectable({ providedIn: 'root' })
export class TokenStorageService {
  private readonly tokenSignal = signal<string | null>(this.leerToken());
  private readonly sesionInvalidada = new Subject<void>();
  readonly token = this.tokenSignal.asReadonly();
  readonly sesionInvalidada$ = this.sesionInvalidada.asObservable();

  guardar(token: string): void {
    this.tokenSignal.set(token);
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      // Almacenamiento no disponible: la sesión queda solo en memoria.
    }
  }

  limpiar(): void {
    this.tokenSignal.set(null);
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USUARIO_KEY);
    } catch {
      // Sin almacenamiento disponible, no hay nada que limpiar.
    }
    this.sesionInvalidada.next();
  }

  private leerToken(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }
}
