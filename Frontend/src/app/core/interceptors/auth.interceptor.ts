import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { API_BASE_URL } from '../api.config';
import { TokenStorageService } from '../auth/token-storage.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const baseUrl = inject(API_BASE_URL).replace(/\/+$/, '');
  const esPeticionApi = req.url === baseUrl || req.url.startsWith(`${baseUrl}/`);
  if (!esPeticionApi) {
    return next(req);
  }

  const tokenStorage = inject(TokenStorageService);
  const router = inject(Router);
  const token = tokenStorage.token();
  const peticion = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(peticion).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        tokenStorage.limpiar();
        void router.navigate(['/login']);
      }
      return throwError(() => error);
    }),
  );
};
