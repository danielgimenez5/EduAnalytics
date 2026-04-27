"""
data_module.py
--------------
Carga, generación y anonimización de datos educativos.
Cumplimiento simulado de GDPR: los datos personales se pseudoanonimizan
antes de cualquier análisis o almacenamiento.
"""

import pandas as pd
import numpy as np
import hashlib
import os
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Generación de datos sintéticos
# ---------------------------------------------------------------------------

NOMBRES = [
    "Ana García", "Carlos Martínez", "Laura Pérez", "Miguel López",
    "Sofía Rodríguez", "Javier Sánchez", "María González", "Pablo Fernández",
    "Elena Díaz", "Andrés Torres", "Isabel Ruiz", "Fernando Morales",
    "Carmen Jiménez", "Luis Hernández", "Rosa Alonso", "David Domínguez",
    "Patricia Vázquez", "Manuel Medina", "Cristina Romero", "Alberto Navarro",
]

ASIGNATURAS = [
    "Matemáticas", "Lengua", "Historia", "Ciencias", "Inglés",
    "Programación", "Estadística", "Física", "Química", "Filosofía",
]


def _pseudoanonimizar_nombre(nombre: str) -> str:
    """Pseudoanonimización GDPR: sustituye nombre real por hash truncado."""
    return "EST-" + hashlib.sha256(nombre.encode()).hexdigest()[:8].upper()


def generar_dataset(n_estudiantes: int = 20, seed: int = 42) -> pd.DataFrame:
    """
    Genera un DataFrame sintético con datos educativos realistas.
    Los nombres se pseudoanonimizan automáticamente (GDPR simulado).
    """
    rng = np.random.default_rng(seed)

    nombres_raw = (NOMBRES * ((n_estudiantes // len(NOMBRES)) + 1))[:n_estudiantes]
    ids = [_pseudoanonimizar_nombre(n) for n in nombres_raw]

    # Perfiles de rendimiento para simular diversidad
    perfiles = rng.choice(["alto", "medio", "bajo"], size=n_estudiantes, p=[0.3, 0.5, 0.2])

    rows = []
    base_date = datetime(2024, 9, 1)

    for i, (sid, perfil) in enumerate(zip(ids, perfiles)):
        if perfil == "alto":
            base_nota = rng.uniform(7.5, 10)
            asistencia = rng.uniform(88, 100)
            participacion = rng.integers(15, 30)
            tareas_entregadas = rng.integers(18, 20)
        elif perfil == "medio":
            base_nota = rng.uniform(5, 8)
            asistencia = rng.uniform(70, 92)
            participacion = rng.integers(7, 18)
            tareas_entregadas = rng.integers(12, 19)
        else:
            base_nota = rng.uniform(2, 6)
            asistencia = rng.uniform(45, 75)
            participacion = rng.integers(1, 8)
            tareas_entregadas = rng.integers(5, 13)

        notas = {asig: round(float(np.clip(base_nota + rng.normal(0, 1), 0, 10)), 2)
                 for asig in ASIGNATURAS}
        nota_media = round(np.mean(list(notas.values())), 2)

        rows.append({
            "id_estudiante": sid,
            "nombre_real": nombres_raw[i],          # Se cifra antes de guardar
            "perfil": perfil,
            "nota_media": nota_media,
            "asistencia_pct": round(float(asistencia), 1),
            "participacion_foro": int(participacion),
            "tareas_entregadas": int(tareas_entregadas),
            "total_tareas": 20,
            "tiempo_plataforma_h": round(float(rng.uniform(10, 120)), 1),
            "ultimo_acceso": (base_date + timedelta(days=int(rng.integers(0, 180)))).strftime("%Y-%m-%d"),
            **{f"nota_{asig.lower().replace(' ', '_')}": v for asig, v in notas.items()},
        })

    df = pd.DataFrame(rows)
    return df


def cargar_csv(path: str) -> pd.DataFrame:
    """Carga un CSV externo y aplica pseudoanonimización si existe columna 'nombre'."""
    df = pd.read_csv(path)
    if "nombre" in df.columns:
        df["nombre_real"] = df["nombre"]
        df["id_estudiante"] = df["nombre"].apply(_pseudoanonimizar_nombre)
        df.drop(columns=["nombre"], inplace=True)
    return df


def calcular_riesgo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula un índice de riesgo de abandono (0–1) basado en heurísticas.
    Se usa también como etiqueta para el modelo ML.
    """
    df = df.copy()
    tasa_tareas = df["tareas_entregadas"] / df["total_tareas"]
    score = (
        (1 - df["nota_media"] / 10) * 0.4
        + (1 - df["asistencia_pct"] / 100) * 0.35
        + (1 - tasa_tareas) * 0.25
    )
    df["indice_riesgo"] = score.round(3)
    df["en_riesgo"] = (df["indice_riesgo"] > 0.4).astype(int)
    return df
