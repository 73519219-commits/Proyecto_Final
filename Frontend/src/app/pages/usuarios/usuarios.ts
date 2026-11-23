import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { mensajeError } from '../../core/http/api-error';
import { rolDesdeTipo } from '../../core/mappers/usuario.mapper';
import { RegistroUsuarioDto, UsuarioUpdateDto } from '../../models/api/usuario.dto';
import { TipoUsuario, Usuario } from '../../models/usuario';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './usuarios.html',
  styleUrl: './usuarios.css',
})
export class UsuariosComponent implements OnInit {
  private readonly usuarioService = inject(UsuarioService);

  readonly usuarios = this.usuarioService.usuarios;
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly editandoId = signal<number | null>(null);

  usuarioForm = new FormGroup({
    nombres: new FormControl('', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]),
    apellidos: new FormControl('', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]),
    email: new FormControl('', [Validators.required, Validators.email, Validators.maxLength(320)]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)]),
    tipo: new FormControl<TipoUsuario>('Negocio', Validators.required),
    telefono: new FormControl('', [Validators.required, Validators.minLength(6), Validators.maxLength(30)]),
    direccion: new FormControl('', [Validators.required, Validators.minLength(5), Validators.maxLength(250)]),
    estado: new FormControl<'Activo' | 'Inactivo'>('Activo', Validators.required),
  });

  ngOnInit(): void {
    this.cargarUsuarios();
  }

  guardarUsuario(): void {
    this.mensaje.set('');
    this.error.set('');

    if (this.usuarioForm.invalid) {
      this.usuarioForm.markAllAsTouched();
      this.error.set('Revise los datos del usuario.');
      return;
    }

    const datos: RegistroUsuarioDto = {
      nombres: this.usuarioForm.value.nombres ?? '',
      apellidos: this.usuarioForm.value.apellidos ?? '',
      correo: this.usuarioForm.value.email ?? '',
      password: this.usuarioForm.value.password ?? '',
      telefono: this.usuarioForm.value.telefono ?? '',
      direccion: this.usuarioForm.value.direccion ?? '',
      rol: rolDesdeTipo(this.usuarioForm.value.tipo ?? 'Negocio'),
      estado: this.usuarioForm.value.estado === 'Inactivo' ? 'inactivo' : 'activo',
    };

    const editandoId = this.editandoId();
    const peticion = editandoId === null
      ? this.usuarioService.registrarUsuario(datos)
      : this.usuarioService.actualizarUsuario(editandoId, {
          ...datos,
          password: datos.password || undefined,
        } satisfies UsuarioUpdateDto);

    peticion.subscribe({
      next: () => {
        this.mensaje.set(editandoId === null ? 'Usuario registrado.' : 'Usuario actualizado.');
        this.resetFormulario();
        this.cargarUsuarios();
      },
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  editarUsuario(usuario: Usuario): void {
    this.editandoId.set(usuario.id);
    this.usuarioForm.controls.password.clearValidators();
    this.usuarioForm.controls.password.setValidators([Validators.minLength(6)]);
    this.usuarioForm.patchValue({
      nombres: usuario.nombres,
      apellidos: usuario.apellidos,
      email: usuario.email,
      password: '',
      tipo: usuario.tipo,
      telefono: usuario.telefono,
      direccion: usuario.direccion,
      estado: usuario.estado,
    });
  }

  eliminarUsuario(id: number): void {
    if (!window.confirm('¿Desea desactivar este usuario?')) {
      return;
    }
    this.mensaje.set('');
    this.error.set('');
    this.usuarioService.eliminarUsuario(id).subscribe({
      next: () => this.mensaje.set('Usuario desactivado.'),
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }

  resetFormulario(): void {
    this.editandoId.set(null);
    this.usuarioForm.controls.password.setValidators([Validators.required, Validators.minLength(6)]);
    this.usuarioForm.reset({
      nombres: '',
      apellidos: '',
      email: '',
      password: '',
      tipo: 'Negocio',
      telefono: '',
      direccion: '',
      estado: 'Activo',
    });
    this.usuarioForm.controls.password.updateValueAndValidity();
  }

  private cargarUsuarios(): void {
    this.usuarioService.listarUsuarios().subscribe({
      error: (error: unknown) => this.error.set(mensajeError(error)),
    });
  }
}
