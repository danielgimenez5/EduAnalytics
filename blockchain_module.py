"""
blockchain_module.py
--------------------
Simulación de blockchain educativa para garantizar la integridad
e inmutabilidad de los registros de aprendizaje.

Cada bloque contiene:
  - Índice y timestamp
  - Hash del bloque anterior (encadenamiento)
  - Datos educativos (puede incluir payload cifrado)
  - Hash propio (SHA-256)
  - Firma digital RSA del bloque

Referencias:
  https://docs.python.org/3/library/hashlib.html
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------------------------
# Bloque individual
# ---------------------------------------------------------------------------

@dataclass
class Bloque:
    index: int
    timestamp: float
    datos: Dict[str, Any]
    hash_anterior: str
    hash_propio: str = field(default="", init=False)
    firma: str = field(default="", init=False)
    nonce: int = field(default=0, init=False)     # Proof-of-Work simplificado

    def __post_init__(self):
        self.hash_propio = self._calcular_hash()

    def _calcular_hash(self) -> str:
        """SHA-256 del contenido canónico del bloque (excluyendo hash_propio y firma)."""
        contenido = {
            "index": self.index,
            "timestamp": self.timestamp,
            "datos": self.datos,
            "hash_anterior": self.hash_anterior,
            "nonce": self.nonce,
        }
        raw = json.dumps(contenido, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def minar(self, dificultad: int = 2) -> None:
        """
        Proof-of-Work simplificado: busca nonce para que el hash
        empiece con 'dificultad' ceros. Dificultad baja para demo.
        """
        prefijo = "0" * dificultad
        while not self.hash_propio.startswith(prefijo):
            self.nonce += 1
            self.hash_propio = self._calcular_hash()

    def es_valido(self) -> bool:
        """Verifica que el hash almacenado coincide con el recalculado."""
        return self.hash_propio == self._calcular_hash()

    def to_dict(self) -> dict:
        return asdict(self)

    def resumen(self) -> dict:
        """Vista reducida para UI."""
        return {
            "Bloque": self.index,
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp)),
            "Hash anterior": self.hash_anterior[:16] + "…",
            "Hash propio": self.hash_propio[:16] + "…",
            "Nonce": self.nonce,
            "Firma": self.firma[:20] + "…" if self.firma else "—",
        }


# ---------------------------------------------------------------------------
# Cadena de bloques
# ---------------------------------------------------------------------------

class BlockchainEducativa:
    """
    Cadena de bloques para registros educativos inmutables.
    - Bloque génesis creado automáticamente.
    - Verificación de integridad de toda la cadena.
    - Soporte para firma RSA de cada bloque.
    """

    DIFICULTAD_POW = 2  # Prefijo de ceros requerido

    def __init__(self):
        self.cadena: List[Bloque] = []
        self._crear_bloque_genesis()

    def _crear_bloque_genesis(self) -> None:
        genesis = Bloque(
            index=0,
            timestamp=time.time(),
            datos={"tipo": "GÉNESIS", "descripcion": "Bloque inicial de la cadena educativa"},
            hash_anterior="0" * 64,
        )
        genesis.minar(self.DIFICULTAD_POW)
        self.cadena.append(genesis)

    # ------------------------------------------------------------------
    # Agregar registros
    # ------------------------------------------------------------------

    def agregar_registro(
        self,
        datos: Dict[str, Any],
        signer=None,          # Instancia de RSASigner (opcional)
    ) -> Bloque:
        """
        Crea y agrega un nuevo bloque con los datos proporcionados.
        Si se pasa un signer, el bloque queda firmado digitalmente.
        """
        ultimo = self.cadena[-1]
        nuevo = Bloque(
            index=len(self.cadena),
            timestamp=time.time(),
            datos=datos,
            hash_anterior=ultimo.hash_propio,
        )
        nuevo.minar(self.DIFICULTAD_POW)

        if signer is not None:
            nuevo.firma = signer.sign(nuevo.hash_propio)

        self.cadena.append(nuevo)
        return nuevo

    def agregar_registro_estudiante(
        self,
        id_estudiante: str,
        evento: str,
        detalles: Dict[str, Any],
        signer=None,
    ) -> Bloque:
        """Wrapper semántico para registros educativos."""
        datos = {
            "id_estudiante": id_estudiante,
            "evento": evento,
            "detalles": detalles,
            "timestamp_legible": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return self.agregar_registro(datos, signer=signer)

    # ------------------------------------------------------------------
    # Verificación de integridad
    # ------------------------------------------------------------------

    def verificar_integridad(self) -> Dict[str, Any]:
        """
        Recorre toda la cadena verificando:
          1. Que cada bloque es internamente válido (hash correcto).
          2. Que el hash_anterior de cada bloque coincide con el hash_propio del anterior.
        """
        errores = []
        for i in range(1, len(self.cadena)):
            actual = self.cadena[i]
            anterior = self.cadena[i - 1]

            if not actual.es_valido():
                errores.append(f"Bloque {i}: hash interno inválido (posible manipulación).")
            if actual.hash_anterior != anterior.hash_propio:
                errores.append(f"Bloque {i}: enlace roto con bloque {i-1}.")

        return {
            "total_bloques": len(self.cadena),
            "integra": len(errores) == 0,
            "errores": errores,
        }

    def manipular_bloque_demo(self, index: int, nuevo_valor: Any) -> None:
        """
        ⚠️  Solo para demostración: altera datos de un bloque para mostrar
        que la verificación de integridad lo detecta.
        """
        if 0 < index < len(self.cadena):
            self.cadena[index].datos["_alterado"] = nuevo_valor

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def get_resumen_cadena(self) -> List[dict]:
        return [b.resumen() for b in self.cadena]

    def get_ultimos_registros(self, n: int = 5) -> List[dict]:
        return [b.to_dict() for b in self.cadena[-n:]]

    def __len__(self) -> int:
        return len(self.cadena)

    def __repr__(self) -> str:
        return f"BlockchainEducativa({len(self.cadena)} bloques)"
