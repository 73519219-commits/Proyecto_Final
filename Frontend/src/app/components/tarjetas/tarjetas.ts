import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-tarjetas',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tarjetas.html',
  styleUrl: './tarjetas.css',
})
export class TarjetasComponent {
  @Input() titulo = 'Resumen';
  @Input() valor: string | number = 0;
  @Input() descripcion = 'Sin descripción';
  @Input() color = 'success';
  @Input() icono = '📦';
}
