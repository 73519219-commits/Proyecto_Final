import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { mensajeError } from '../../core/http/api-error';
import { rolDesdeTipo } from '../../core/mappers/usuario.mapper';
import { RegistroUsuarioDto } from '../../models/api/usuario.dto';
import { UsuarioService } from '../../services/usuario';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './registro.html',
  styleUrl: './registro.css',
})
export class RegistroComponent {
  private readonly usuarioService = inject(UsuarioService);
  private readonly router = inject(Router);
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly guardando = signal(false);

  registroForm = new FormGroup({
    nombres: new FormControl('', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]),
    apellidos: new FormControl('', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]),
    email: new FormControl('', [Validators.required, Validators.email, Validators.maxLength(320)]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)]),
    tipo: new FormControl('Negocio', Validators.required),
    telefono: new FormControl('', [Validators.required, Validators.minLength(6), Validators.maxLength(30)]),
    direccion: new FormControl('', [Validators.required, Validators.minLength(5), Validators.maxLength(250)]),
  });

  guardarUsuario(): void {
    this.mensaje.set('');
    this.error.set('');

    if (this.registroForm.invalid) {
      this.registroForm.markAllAsTouched();
      this.error.set('Complete los datos obligatorios correctamente.');
      return;
    }

    const datos: RegistroUsuarioDto = {
      nombres: this.registroForm.value.nombres ?? '',
      apellidos: this.registroForm.value.apellidos ?? '',
      correo: this.registroForm.value.email ?? '',
      password: this.registroForm.value.password ?? '',
      telefono: this.registroForm.value.telefono ?? '',
      direccion: this.registroForm.value.direccion ?? '',
      rol: rolDesdeTipo(this.registroForm.value.tipo ?? 'Negocio'),
      estado: 'activo',
    };

    this.guardando.set(true);
    this.usuarioService.registrarUsuario(datos).subscribe({
      next: () => {
        this.guardando.set(false);
        this.mensaje.set('Usuario registrado correctamente.');
        this.registroForm.reset({ tipo: 'Negocio' });
        setTimeout(() => this.router.navigate(['/login']), 1000);
      },
      error: (error: unknown) => {
        this.guardando.set(false);
        this.error.set(mensajeError(error));
      },
    });
  }
}
