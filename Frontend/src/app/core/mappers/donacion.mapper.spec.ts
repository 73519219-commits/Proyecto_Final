import { estadoDonacionDto, toDonacion } from './donacion.mapper';

describe('donacion.mapper', () => {
  it('mapea los campos del backend al modelo de la UI', () => {
    const donacion = toDonacion({
      id: 1,
      nombre_alimento: 'Pan de trigo',
      descripcion: 'Pan recién horneado',
      cantidad: 40,
      unidad: 'unidad',
      fecha_vencimiento: '2026-12-01',
      direccion_recojo: 'Av. Real 320',
      hora_disponible: '08:00 - 10:00',
      estado: 'entregada',
      usuario_negocio_id: 2,
    });

    expect(donacion.nombreAlimento).toBe('Pan de trigo');
    expect(donacion.unidadMedida).toBe('unidad');
    expect(donacion.direccionRecogida).toBe('Av. Real 320');
    expect(donacion.donanteId).toBe(2);
    expect(donacion.estado).toBe('Entregada');
  });

  it('traduce los estados de la UI al contrato del backend', () => {
    expect(estadoDonacionDto('Disponible')).toBe('disponible');
    expect(estadoDonacionDto('Reservada')).toBe('reservada');
    expect(estadoDonacionDto('Cancelada')).toBe('cancelada');
    expect(estadoDonacionDto('Entregada')).toBe('entregada');
  });
});
