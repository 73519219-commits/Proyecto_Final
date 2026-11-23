from datetime import datetime

from pydantic import BaseModel


class AvisoOut(BaseModel):
    id: int
    usuario_destino: int
    tipo: str
    mensaje: str
    referencia_id: int | None
    leido: bool
    created_at: datetime
