import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class SidebarComponent {
  readonly usuarioService = inject(UsuarioService);
  readonly usuarioActual = this.usuarioService.usuarioActual;

  readonly itemsMenu = computed(() => {
    const tipo = this.usuarioActual()?.tipo ?? 'Visitante';

    if (this.usuarioService.esAdmin(tipo)) {
      return [
        { label: 'Dashboard', ruta: '/dashboard' },
        { label: 'Usuarios', ruta: '/usuarios' },
        { label: 'Donaciones', ruta: '/donaciones' },
        { label: 'Solicitudes', ruta: '/solicitudes' },
        { label: 'Voluntarios', ruta: '/voluntarios' },
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
      { label: 'Iniciar sesión', ruta: '/login' },
    ];
  });
}
