"""
crypto_module.py
----------------
Módulo de criptografía para proteger datos educativos sensibles.

Implementa:
  - Encriptación simétrica AES-256-GCM (confidencialidad + autenticidad)
  - Firmas digitales RSA-2048 con PKCS#1v15 + SHA-256 (no repudio)
  - Gestión segura de claves (nunca expuestas en logs o UI)

Referencias:
  https://cryptography.io/en/latest/
"""

import os
import json
import base64
from typing import Tuple, Dict, Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag


# ---------------------------------------------------------------------------
# AES-256-GCM — Encriptación simétrica autenticada
# ---------------------------------------------------------------------------

class AESCipher:
    """
    Cifrado simétrico AES-256-GCM.
    - Clave de 256 bits generada aleatoriamente.
    - Nonce único por operación (96 bits).
    - GCM proporciona autenticación integrada (AEAD).
    """

    KEY_SIZE = 32  # 256 bits

    def __init__(self, key: bytes = None):
        self._key = key if key is not None else os.urandom(self.KEY_SIZE)
        self._aesgcm = AESGCM(self._key)

    # ------------------------------------------------------------------
    # Propiedades públicas (la clave nunca se expone como string plano)
    # ------------------------------------------------------------------

    def export_key_b64(self) -> str:
        """Exporta la clave como Base64 (para almacenamiento seguro fuera de código)."""
        return base64.b64encode(self._key).decode()

    @classmethod
    def from_key_b64(cls, key_b64: str) -> "AESCipher":
        return cls(key=base64.b64decode(key_b64))

    # ------------------------------------------------------------------
    # Operaciones de cifrado
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: str) -> Dict[str, str]:
        """
        Cifra texto plano.
        Devuelve dict con nonce y ciphertext en Base64.
        """
        nonce = os.urandom(12)  # 96 bits — recomendado por NIST para GCM
        ct = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        return {
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ct).decode(),
        }

    def decrypt(self, payload: Dict[str, str]) -> str:
        """
        Descifra payload {nonce, ciphertext}.
        Lanza InvalidTag si los datos han sido manipulados.
        """
        nonce = base64.b64decode(payload["nonce"])
        ct = base64.b64decode(payload["ciphertext"])
        try:
            return self._aesgcm.decrypt(nonce, ct, None).decode()
        except InvalidTag:
            raise ValueError("❌ Autenticación fallida: los datos pueden haber sido alterados.")

    def encrypt_json(self, data: Any) -> Dict[str, str]:
        """Cifra cualquier objeto serializable como JSON."""
        return self.encrypt(json.dumps(data, ensure_ascii=False))

    def decrypt_json(self, payload: Dict[str, str]) -> Any:
        return json.loads(self.decrypt(payload))


# ---------------------------------------------------------------------------
# RSA-2048 — Firma digital
# ---------------------------------------------------------------------------

class RSASigner:
    """
    Firma y verificación RSA-2048 con PKCS#1v15 + SHA-256.
    Garantiza autenticidad e integridad de los registros educativos.
    """

    KEY_SIZE = 2048

    def __init__(self):
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.KEY_SIZE,
            backend=default_backend(),
        )
        self._public_key = self._private_key.public_key()

    # ------------------------------------------------------------------
    # Exportación de claves (PEM)
    # ------------------------------------------------------------------

    def export_public_key_pem(self) -> str:
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def export_private_key_pem(self) -> str:
        """⚠️  Solo para almacenamiento seguro — nunca mostrar en UI."""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

    # ------------------------------------------------------------------
    # Firma y verificación
    # ------------------------------------------------------------------

    def sign(self, message: str) -> str:
        """Firma un mensaje y devuelve la firma en Base64."""
        signature = self._private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def verify(self, message: str, signature_b64: str) -> bool:
        """
        Verifica una firma RSA.
        Devuelve True si es válida, False si no.
        """
        try:
            self._public_key.verify(
                base64.b64decode(signature_b64),
                message.encode(),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Utilidad: cifrar columnas de un DataFrame
# ---------------------------------------------------------------------------

def cifrar_columnas_df(df, columnas: list, cipher: AESCipher) -> dict:
    """
    Cifra las columnas indicadas de un DataFrame.
    Devuelve dict: {id_estudiante: {columna: payload_cifrado}}
    No modifica el DataFrame original.
    """
    registros_cifrados = {}
    for _, row in df.iterrows():
        sid = row["id_estudiante"]
        registros_cifrados[sid] = {}
        for col in columnas:
            if col in row.index:
                registros_cifrados[sid][col] = cipher.encrypt(str(row[col]))
    return registros_cifrados


def descifrar_registro(registro_cifrado: dict, cipher: AESCipher) -> dict:
    """Descifra un registro individual."""
    return {col: cipher.decrypt(payload) for col, payload in registro_cifrado.items()}
