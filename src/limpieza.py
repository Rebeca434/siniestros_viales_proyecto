"""
limpieza.py
Limpieza, normalización y conversión del dataset ATUS-INEGI.
Soporta CSV (del INEGI real) o Parquet (generado/previo).
"""
import pandas as pd
import os
import sys
import time


# ── Columnas esperadas del INEGI real (ATUS) ─────────────────────────────────
# Ajusta este mapeo al CSV real que descargues del INEGI.
# Clave_real → nombre interno usado por el proyecto
MAPA_COLUMNAS_INEGI = {
    "ID_ACCIDENTE":   "id_accidente",
    "ANIO":           "anio",
    "MES":            "mes",
    "DIA":            "dia",
    "HORA":           "hora",
    "ENTIDAD":        "entidad_nombre",
    "CVE_ENT":        "entidad_clave",
    "MUNICIPIO":      "municipio",
    "CAUSAACCID":     "causa",
    "TIPACCID":       "tipo_accidente",
    "CONDVIAL":       "condicion_via",
    "NEHERIDOS":      "heridos",
    "NEMUERTOS":      "fallecidos",
}

COLUMNAS_REQUERIDAS = [
    "id_accidente", "anio", "mes", "dia", "hora",
    "entidad_nombre", "entidad_clave", "municipio",
    "causa", "tipo_accidente", "heridos", "fallecidos",
]


def cargar_datos(ruta: str) -> pd.DataFrame:
    """Carga CSV o Parquet y aplica el mapeo de columnas si es necesario."""
    ext = os.path.splitext(ruta)[1].lower()
    t0 = time.time()

    if ext in (".parquet", ".pq"):
        df = pd.read_parquet(ruta)
    elif ext == ".csv":
        df = pd.read_csv(ruta, encoding="latin-1", low_memory=False)
        # Normalizar nombres de columnas a minúsculas
        df.columns = [c.strip().upper() for c in df.columns]
        # Aplicar mapeo si coincide con estructura INEGI
        df.rename(columns=MAPA_COLUMNAS_INEGI, inplace=True)
    else:
        raise ValueError(f"Formato no soportado: {ext}. Use .csv o .parquet")

    print(f"  Carga: {len(df):,} filas en {time.time()-t0:.2f}s")
    return df


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza y normalización:
      - Elimina duplicados
      - Fuerza tipos numéricos
      - Rellena nulos en campos clave
      - Agrega columnas derivadas (con_heridos, con_fallecidos)
      - Crea columna 'fecha' de tipo datetime
    """
    n_orig = len(df)

    # ── 1. Eliminar duplicados ────────────────────────────────────────────────
    df = df.drop_duplicates(subset=["id_accidente"], keep="first").copy()

    # ── 2. Convertir tipos numéricos ──────────────────────────────────────────
    for col in ["anio", "mes", "dia", "hora", "heridos", "fallecidos",
                "entidad_clave", "municipio"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── 3. Rangos válidos ─────────────────────────────────────────────────────
    df = df[df["mes"].between(1, 12)]
    df = df[df["dia"].between(1, 31)]
    df = df[df["hora"].between(0, 23)]

    # ── 4. Nulos en texto ─────────────────────────────────────────────────────
    for col in ["entidad_nombre", "causa", "tipo_accidente", "condicion_via"]:
        if col in df.columns:
            df[col] = df[col].fillna("No especificado").str.strip()

    # ── 5. Nulos numéricos ────────────────────────────────────────────────────
    df["heridos"]    = df["heridos"].fillna(0).astype(int).clip(lower=0)
    df["fallecidos"] = df["fallecidos"].fillna(0).astype(int).clip(lower=0)
    df["municipio"]  = df["municipio"].fillna(0).astype(int)

    # ── 6. Columnas derivadas ─────────────────────────────────────────────────
    df["con_heridos"]    = (df["heridos"]    > 0).astype(int)
    df["con_fallecidos"] = (df["fallecidos"] > 0).astype(int)

    # ── 7. Fecha ──────────────────────────────────────────────────────────────
    try:
        df["fecha"] = pd.to_datetime(
            df[["anio", "mes", "dia"]].rename(
                columns={"anio": "year", "mes": "month", "dia": "day"}
            ),
            errors="coerce",
        )
    except Exception:
        df["fecha"] = pd.NaT

    n_fin = len(df)
    print(f"  Limpieza: {n_orig:,} → {n_fin:,} filas "
          f"(descartados {n_orig - n_fin:,})")
    return df.reset_index(drop=True)


def guardar_parquet(df: pd.DataFrame, ruta: str) -> None:
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    df.to_parquet(ruta, index=False)
    print(f"  Guardado en {ruta}  ({os.path.getsize(ruta)/1e6:.1f} MB)")


def pipeline(ruta_entrada: str, ruta_salida: str) -> pd.DataFrame:
    print("── Módulo de limpieza ──────────────────────────────────────────")
    df = cargar_datos(ruta_entrada)
    df = limpiar(df)
    guardar_parquet(df, ruta_salida)
    print("── Limpieza completada ─────────────────────────────────────────\n")
    return df


if __name__ == "__main__":
    entrada = sys.argv[1] if len(sys.argv) > 1 else "data/accidentes_atus.parquet"
    salida  = sys.argv[2] if len(sys.argv) > 2 else "data/accidentes_limpio.parquet"
    pipeline(entrada, salida)
