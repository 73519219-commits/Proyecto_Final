import { InjectionToken } from '@angular/core';
import { environment } from '../../environments/environment';

/**
 * URL base de FastAPI (incluye el prefijo `/api`).
 * Los servicios la inyectan en lugar de importar `environment` directamente.
 */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => environment.apiUrl,
});
