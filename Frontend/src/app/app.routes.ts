import { CanActivateFn, Router, Routes } from '@angular/router';
import { inject } from '@angular/core';
import { UsuarioService } from './services/usuario';
import { InicioComponent } from './pages/inicio/inicio';
import { LoginComponent } from './pages/login/login';
import { RegistroComponent } from './pages/registro/registro';
import { DashboardComponent } from './pages/dashboard/dashboard';
import { DonacionesComponent } from './pages/donaciones/donaciones';
import { SolicitudesComponent } from './pages/solicitudes/solicitudes';
import { VoluntariosComponent } from './pages/voluntarios/voluntarios';
import { UsuariosComponent } from './pages/usuarios/usuarios';

export const authGuard: CanActivateFn = () => {
  const usuarioService = inject(UsuarioService);
  const router = inject(Router);

  if (usuarioService.usuarioActual()) {
    return true;
  }

  return router.createUrlTree(['/login']);
};

export const adminGuard: CanActivateFn = () => {
  const usuarioService = inject(UsuarioService);
  const router = inject(Router);
  const usuarioActual = usuarioService.usuarioActual();

  if (!usuarioActual) {
    return router.createUrlTree(['/login']);
  }

  if (!usuarioService.esAdmin(usuarioActual.tipo)) {
    return router.createUrlTree(['/dashboard']);
  }

  return true;
};

export const negocioGuard: CanActivateFn = () => {
  const usuarioService = inject(UsuarioService);
  const router = inject(Router);
  const usuarioActual = usuarioService.usuarioActual();

  if (!usuarioActual) {
    return router.createUrlTree(['/login']);
  }

  if (!usuarioService.esAdmin(usuarioActual.tipo) && !usuarioService.esNegocio(usuarioActual.tipo)) {
    return router.createUrlTree(['/dashboard']);
  }

  return true;
};

export const comedorGuard: CanActivateFn = () => {
  const usuarioService = inject(UsuarioService);
  const router = inject(Router);
  const usuarioActual = usuarioService.usuarioActual();

  if (!usuarioActual) {
    return router.createUrlTree(['/login']);
  }

  if (!usuarioService.esAdmin(usuarioActual.tipo) && !usuarioService.esComedor(usuarioActual.tipo)) {
    return router.createUrlTree(['/dashboard']);
  }

  return true;
};

export const voluntarioGuard: CanActivateFn = () => {
  const usuarioService = inject(UsuarioService);
  const router = inject(Router);
  const usuarioActual = usuarioService.usuarioActual();

  if (!usuarioActual) {
    return router.createUrlTree(['/login']);
  }

  if (!usuarioService.esAdmin(usuarioActual.tipo) && !usuarioService.esVoluntario(usuarioActual.tipo)) {
    return router.createUrlTree(['/dashboard']);
  }

  return true;
};

export const routes: Routes = [
  { path: '', component: InicioComponent },
  { path: 'login', component: LoginComponent },
  { path: 'registro', component: RegistroComponent },
  { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
  { path: 'donaciones', component: DonacionesComponent, canActivate: [authGuard, negocioGuard] },
  { path: 'solicitudes', component: SolicitudesComponent, canActivate: [authGuard, comedorGuard] },
  { path: 'voluntarios', component: VoluntariosComponent, canActivate: [authGuard, voluntarioGuard] },
  { path: 'usuarios', component: UsuariosComponent, canActivate: [authGuard, adminGuard] },
  { path: '**', redirectTo: '' },
];
