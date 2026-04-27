# 🎓 EduAnalytics Platform

> **Trabajo académico** — Asignatura: *Análisis de Datos II: Criptografía, Blockchain y Learning Analytics*
>
> Herramienta de Learning Analytics con integración de Criptografía y Blockchain, desarrollada en Python + Streamlit.

---

## 📋 Descripción del Proyecto

**EduAnalytics** es una plataforma de análisis educativo que demuestra la integración práctica de tres áreas:

| Área | Tecnología | Objetivo |
|------|-----------|----------|
| **Learning Analytics** | Pandas · Scikit-learn · Matplotlib | Análisis de rendimiento y predicción de riesgo |
| **Criptografía** | AES-256-GCM · RSA-2048 | Protección de datos educativos sensibles (GDPR) |
| **Blockchain** | SHA-256 · Proof-of-Work | Inmutabilidad e integridad de registros académicos |

### Público objetivo
Docentes y administradores educativos de plataformas de aprendizaje en línea que necesiten:
- Monitorizar el rendimiento estudiantil con privacidad garantizada.
- Asegurar la integridad de los registros académicos.
- Identificar estudiantes en riesgo de abandono de forma proactiva.

---

## 🏗️ Arquitectura del proyecto

```
learning_analytics_project/
│
├── app.py                  # Interfaz principal Streamlit (iOS 26 design)
├── data_module.py          # Generación, carga y anonimización de datos
├── crypto_module.py        # AES-256-GCM + RSA-2048
├── blockchain_module.py    # Simulación blockchain con SHA-256
├── analytics_module.py     # Learning Analytics + modelo Random Forest
├── requirements.txt        # Dependencias Python
└── README.md
```

---

## ⚙️ Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/danielgimenez5/eduanalytics-platform.git
cd eduanalytics-platform
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

La app se abrirá en `http://localhost:8501`.

---

## 🔐 Módulo de Criptografía (`crypto_module.py`)

### AES-256-GCM — Cifrado simétrico autenticado

```python
from crypto_module import AESCipher

cipher = AESCipher()                          # Genera clave aleatoria de 256 bits
payload = cipher.encrypt("Nota: 8.5 · Ana")  # Cifra → {nonce, ciphertext}
texto   = cipher.decrypt(payload)             # Descifra y verifica autenticidad
```

- **Modo GCM**: Proporciona cifrado + autenticación en una sola operación (AEAD).
- **Nonce de 96 bits**: Único por operación, generado con `os.urandom(12)`.
- **Integridad**: Si el ciphertext es modificado, `InvalidTag` es lanzada automáticamente.

### RSA-2048 — Firma digital

```python
from crypto_module import RSASigner

signer    = RSASigner()
firma     = signer.sign("Registro académico oficial")
es_valida = signer.verify("Registro académico oficial", firma)  # True
```

- **PKCS#1v15 + SHA-256**: Estándar ampliamente compatible.
- **Clave de 2048 bits**: Balance entre seguridad y rendimiento.

---

## ⛓️ Módulo Blockchain (`blockchain_module.py`)

Cada bloque contiene:
- `index` + `timestamp`
- `hash_anterior` (encadenamiento)
- `datos` (registro educativo)
- `hash_propio` (SHA-256 del contenido)
- `nonce` (Proof-of-Work simplificado)
- `firma` (RSA opcional)

```python
from blockchain_module import BlockchainEducativa

bc = BlockchainEducativa()
bc.agregar_registro_estudiante("EST-A1B2C3D4", "CALIFICACIÓN", {"nota": 8.5})
resultado = bc.verificar_integridad()  # {"integra": True, "total_bloques": 2}
```

### Proof-of-Work
El minado requiere que el hash empiece con `00` (dificultad = 2), simulando el mecanismo de consenso de Bitcoin a escala de demostración.

---

## 📊 Módulo de Analytics (`analytics_module.py`)

### Índice de Riesgo (heurístico)
```
riesgo = nota_baja × 0.40 + baja_asistencia × 0.35 + tareas_pendientes × 0.25
```

Estudiante marcado **en riesgo** si `índice > 0.40`.

### Modelo ML — Random Forest

| Hiperparámetro | Valor |
|---|---|
| `n_estimators` | 100 |
| `max_depth` | 5 |
| `class_weight` | balanced |
| `test_size` | 25% |

**Features usadas**: nota_media, asistencia_pct, participacion_foro, tareas_entregadas, tiempo_plataforma_h.

---

## 🛡️ Consideraciones éticas y GDPR (simulado)

| Principio | Implementación |
|---|---|
| **Pseudoanonimización** | Los nombres reales se sustituyen por `EST-{hash8}` (SHA-256 truncado) |
| **Minimización de datos** | Solo se procesan las variables necesarias para el análisis |
| **Cifrado en reposo** | Datos sensibles cifrados con AES-256-GCM |
| **Trazabilidad** | Cada acceso/modificación queda registrado en la blockchain |
| **No-repudio** | Registros firmados digitalmente con RSA |

---

## 📚 Referencias

- [Python Cryptography Library](https://cryptography.io/en/latest/)
- [Hashlib — Python 3 docs](https://docs.python.org/3/library/hashlib.html)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Scikit-learn Documentation](https://scikit-learn.org/stable/documentation.html)
- [JISC Code of Practice for Learning Analytics](https://www.jisc.ac.uk/guides/code-of-practice-for-learning-analytics)
- NIST SP 800-38D — Recommendation for Block Cipher Modes: GCM
- RFC 8017 — PKCS #1: RSA Cryptography Specifications

---

## 👨‍💻 Autor

**Daniel Giménez** — [@danielgimenez5](https://github.com/danielgimenez5)

*Grado en Ciencia de Datos / Análisis de Datos II — Curso 2024–25*

---

## 📄 Licencia

MIT License — uso académico y educativo.
