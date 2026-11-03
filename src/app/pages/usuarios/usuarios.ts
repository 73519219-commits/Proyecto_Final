import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { Usuario, TipoUsuario } from '../../models/usuario';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './usuarios.html',
  styleUrl: './usuarios.css',
})
export class UsuariosComponent {
  private readonly usuarioService = inject(UsuarioService);
  readonly usuarios = this.usuarioService.usuarios;
  readonly mensaje = signal('');
  readonly modoEdicion = signal<number | null>(null);

  usuarioForm = new FormGroup({
    nombre: new FormControl('', Validators.required),
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)]),
    tipo: new FormControl<TipoUsuario>('Negocio', Validators.required),
    telefono: new FormControl('', Validators.required),
    direccion: new FormControl('', Validators.required),
    empresa: new FormControl(''),
    estado: new FormControl<'Activo' | 'Inactivo'>('Activo', Validators.required),
  });

  guardarUsuario(): void {
    if (this.usuarioForm.invalid) {
      this.usuarioForm.markAllAsTouched();
      this.mensaje.set('Revise los datos del usuario.');
      return;
    }

    const usuario: Usuario = {
      id: this.modoEdicion() ?? Date.now(),
      nombre: this.usuarioForm.value.nombre ?? '',
      email: this.usuarioForm.value.email ?? '',
      password: this.usuarioForm.value.password ?? '',
      tipo: (this.usuarioForm.value.tipo as TipoUsuario) ?? 'Negocio',
      telefono: this.usuarioForm.value.telefono ?? '',
      direccion: this.usuarioForm.value.direccion ?? '',
      empresa: this.usuarioForm.value.empresa ?? '',
      estado: (this.usuarioForm.value.estado as 'Activo' | 'Inactivo') ?? 'Activo',
    };

    if (this.modoEdicion() !== null) {
      this.usuarioService.actualizarUsuario(this.modoEdicion()!, usuario);
      this.mensaje.set('Usuario actualizado.');
    } else {
      this.usuarioService.registrarUsuario(usuario);
      this.mensaje.set('Usuario registrado.');
    }

    this.resetFormulario();
  }

  editarUsuario(usuario: Usuario): void {
    this.modoEdicion.set(usuario.id);
    this.usuarioForm.patchValue(usuario);
  }

  eliminarUsuario(id: number): void {
    this.usuarioService.eliminarUsuario(id);
    this.mensaje.set('Usuario eliminado.');
  }

  resetFormulario(): void {
    this.modoEdicion.set(null);
    this.usuarioForm.reset({
      nombre: '',
      email: '',
      password: '',
      tipo: 'Negocio',
      telefono: '',
      direccion: '',
      empresa: '',
      estado: 'Activo',
    });
  }
}
