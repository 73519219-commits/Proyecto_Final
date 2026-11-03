import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
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

  registroForm = new FormGroup({
    nombre: new FormControl('', Validators.required),
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)]),
    tipo: new FormControl('Negocio', Validators.required),
    telefono: new FormControl('', Validators.required),
    direccion: new FormControl('', Validators.required),
    empresa: new FormControl(''),
  });

  get tipoSeleccionado(): string {
    return this.registroForm.get('tipo')?.value || 'Negocio';
  }

  guardarUsuario(): void {
    if (this.registroForm.invalid) {
      this.registroForm.markAllAsTouched();
      this.mensaje.set('Complete los datos obligatorios correctamente.');
      return;
    }

    const nuevoUsuario = {
      id: Date.now(),
      nombre: this.registroForm.value.nombre ?? '',
      email: this.registroForm.value.email ?? '',
      password: this.registroForm.value.password ?? '',
      tipo: this.registroForm.value.tipo as any,
      telefono: this.registroForm.value.telefono ?? '',
      direccion: this.registroForm.value.direccion ?? '',
      empresa: this.registroForm.value.empresa || this.registroForm.value.nombre || '',
      estado: 'Activo' as const,
    };

    this.usuarioService.registrarUsuario(nuevoUsuario);
    this.mensaje.set('Usuario registrado correctamente.');
    this.registroForm.reset({ tipo: 'Negocio' });
    setTimeout(() => this.router.navigate(['/login']), 1000);
  }
}
