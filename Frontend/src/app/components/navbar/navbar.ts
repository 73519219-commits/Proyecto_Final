import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { interval, Subscription } from 'rxjs';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { UsuarioService } from '../../services/usuario';
import { AvisoService } from '../../services/aviso';
import { mensajeError } from '../../core/http/api-error';
import { TokenStorageService } from '../../core/auth/token-storage.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css',
})
export class NavbarComponent implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  readonly usuarioService = inject(UsuarioService);
  readonly usuarioActual = this.usuarioService.usuarioActual;
  private readonly tokenStorage = inject(TokenStorageService);
  private readonly avisoService = inject(AvisoService);
  readonly avisos = this.avisoService.avisos;
  readonly errorAviso = signal('');
  readonly avisosAbiertos = signal(false);
  readonly noLeidos = computed(() => this.avisos().filter((aviso) => !aviso.leido).length);
  private refresco?: Subscription;
  private sesionInvalidada?: Subscription;

  ngOnInit(): void {
    if (this.usuarioActual()) this.cargarAvisos();
    this.sesionInvalidada = this.tokenStorage.sesionInvalidada$.subscribe(() => {
      this.errorAviso.set('');
      this.avisosAbiertos.set(false);
    });
    this.refresco = interval(30000).subscribe(() => {
      if (this.usuarioActual()) this.cargarAvisos();
    });
  }

  ngOnDestroy(): void {
    this.refresco?.unsubscribe();
    this.sesionInvalidada?.unsubscribe();
  }

  cargarAvisos(): void {
    this.avisoService.listar().subscribe({
      next: () => this.errorAviso.set(''),
      error: (error: unknown) => this.errorAviso.set(mensajeError(error)),
    });
  }

  abrirAvisos(): void {
    this.avisosAbiertos.update((abierto) => !abierto);
    if (this.avisosAbiertos()) {
      for (const aviso of this.avisos().filter((item) => !item.leido)) {
        this.avisoService.marcarLeido(aviso.id).subscribe({
          error: (error: unknown) => this.errorAviso.set(mensajeError(error)),
        });
      }
    }
  }

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
      ];
    }

    if (this.usuarioService.esComedor(tipo)) {
      return [
        { label: 'Dashboard', ruta: '/dashboard' },
        { label: 'Solicitudes', ruta: '/solicitudes' },
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
