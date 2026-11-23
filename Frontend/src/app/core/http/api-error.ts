import { HttpErrorResponse } from '@angular/common/http';

interface ErrorValidacion {
  msg?: string;
}

/**
 * Traduce los errores de FastAPI (`detail`) a un mensaje legible.
 * Soporta `detail` como texto y como lista de validación de Pydantic.
 */
export function mensajeError(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. Verifique que FastAPI esté en ejecución.';
    }

    const detalle = (error.error as { detail?: unknown } | null)?.detail;

    if (typeof detalle === 'string') {
      return detalle;
    }

    if (Array.isArray(detalle)) {
      const mensajes = (detalle as ErrorValidacion[])
        .map((item) => item.msg)
        .filter((msg): msg is string => Boolean(msg));
      if (mensajes.length > 0) {
        return mensajes.join(' ');
      }
    }

    return `Error ${error.status}: ${error.statusText || 'solicitud rechazada'}`;
  }

  return 'Ocurrió un error inesperado.';
}
