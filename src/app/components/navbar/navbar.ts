import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class NavbarComponent {
  private readonly router = inject(Router);
  readonly usuarioService = inject(UsuarioService);
  readonly usuarioActual = this.usuarioService.usuarioActual;

  readonly itemsMenu = computed(() => {
    const usuario = this.usuarioActual();
    if (!usuario) {
      return [
        { label: 'Inicio', ruta: '/' },
        { label: 'Iniciar sesión', ruta: '/login' },
        { label: 'Registrarse', ruta: '/registro' },
      ];
    }

    const tipo = usuario.tipo;

    if (this.usuarioService.esAdmin(tipo)) {
      return [
        { label: 'Dashboard', ruta: '/dashboard' },
        { label: 'Donaciones', ruta: '/donaciones' },
        { label: 'Solicitudes', ruta: '/solicitudes' },
        { label: 'Voluntarios', ruta: '/voluntarios' },
        { label: 'Usuarios', ruta: '/usuarios' },
      ];
    }

    if (this.usuarioService.esNegocio(tipo)) {
      return [
        { label: 'Dashboard', ruta: '/dashboard' },
        { label: 'Mis donaciones', ruta: '/donaciones' },
        { label: 'Solicitudes', ruta: '/solicitudes' },
      ];
    }

    if (this.usuarioService.esComedor(tipo)) {
      return [
        { label: 'Dashboard', ruta: '/dashboard' },
        { label: 'Solicitudes', ruta: '/solicitudes' },
        { label: 'Voluntarios', ruta: '/voluntarios' },
      ];
    }

    if (this.usuarioService.esVoluntario(tipo)) {
      return [
        { label: 'Dashboard', ruta: '/dashboard' },
        { label: 'Entregas', ruta: '/voluntarios' },
      ];
    }

    return [
      { label: 'Inicio', ruta: '/' },
      { label: 'Dashboard', ruta: '/dashboard' },
    ];
  });

  cerrarSesion(): void {
    this.usuarioService.cerrarSesion();
    this.router.navigate(['/login']);
  }
}
