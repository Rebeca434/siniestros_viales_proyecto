"""
generar_datos.py
Genera un dataset sintético de accidentes viales con estructura ATUS-INEGI.
Úsalo si no tienes el CSV real del INEGI o para pruebas rápidas.
"""
import pandas as pd
import numpy as np
import os

# ─────────────────────────────────────────────
SEMILLA   = 42
N_FILAS   = 500_000   # cambia a 2_000_000 para prueba de carga
ANIOS     = list(range(2018, 2024))
RUTA_OUT  = "data/accidentes_atus.parquet"
# ─────────────────────────────────────────────

ESTADOS = {
    "Aguascalientes": 1, "Baja California": 2, "Baja California Sur": 3,
    "Campeche": 4, "Coahuila": 5, "Colima": 6, "Chiapas": 7,
    "Chihuahua": 8, "Ciudad de México": 9, "Durango": 10,
    "Guanajuato": 11, "Guerrero": 12, "Hidalgo": 13, "Jalisco": 14,
    "México": 15, "Michoacán": 16, "Morelos": 17, "Nayarit": 18,
    "Nuevo León": 19, "Oaxaca": 20, "Puebla": 21, "Querétaro": 22,
    "Quintana Roo": 23, "San Luis Potosí": 24, "Sinaloa": 25,
    "Sonora": 26, "Tabasco": 27, "Tamaulipas": 28, "Tlaxcala": 29,
    "Veracruz": 30, "Yucatán": 31, "Zacatecas": 32,
}

CAUSAS = [
    "Exceso de velocidad", "Conductor ebrio", "No respetar señales",
    "Distracciones al manejar", "Falla mecánica", "Mal estado de la vía",
    "Invasión de carril", "Rebaso indebido", "Giro incorrecto",
    "Otra causa",
]

TIPOS = ["Colisión con vehículo", "Atropellamiento", "Volcadura",
         "Colisión con objeto fijo", "Salida del camino", "Otro"]

CONDICIONES = ["Buenas", "Lluvia", "Neblina", "Noche sin alumbrado"]

def generar_dataset(n: int = N_FILAS, semilla: int = SEMILLA) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    n_estados = len(ESTADOS)
    nombres = list(ESTADOS.keys())
    claves  = list(ESTADOS.values())

    # Distribución no uniforme: CDMX, Jalisco, Estado de México tienen más accidentes
    pesos = np.ones(n_estados)
    for i, nm in enumerate(nombres):
        if nm in ("Ciudad de México", "Jalisco", "México", "Nuevo León", "Veracruz"):
            pesos[i] = 5
        elif nm in ("Chihuahua", "Puebla", "Guanajuato"):
            pesos[i] = 3
    pesos /= pesos.sum()

    idx_estado = rng.choice(n_estados, size=n, p=pesos)

    anio  = rng.choice(ANIOS, size=n)
    mes   = rng.integers(1, 13, size=n)
    dia   = rng.integers(1, 29, size=n)
    hora  = rng.integers(0, 24, size=n)

    # Heridos y fallecidos – Poisson con lambda bajo
    heridos    = rng.poisson(0.8, size=n)
    fallecidos = rng.poisson(0.05, size=n)

    df = pd.DataFrame({
        "id_accidente":   np.arange(1, n + 1),
        "anio":           anio,
        "mes":            mes,
        "dia":            dia,
        "hora":           hora,
        "entidad_nombre": [nombres[i] for i in idx_estado],
        "entidad_clave":  [claves[i]  for i in idx_estado],
        "municipio":      rng.integers(1, 15, size=n),   # clave simplificada
        "causa":          rng.choice(CAUSAS, size=n),
        "tipo_accidente": rng.choice(TIPOS,  size=n),
        "condicion_via":  rng.choice(CONDICIONES, size=n),
        "heridos":        heridos,
        "fallecidos":     fallecidos,
        "con_heridos":    (heridos > 0).astype(int),
        "con_fallecidos": (fallecidos > 0).astype(int),
    })
    return df


def main():
    os.makedirs("data", exist_ok=True)
    print(f"Generando {N_FILAS:,} registros sintéticos…")
    df = generar_dataset()
    df.to_parquet(RUTA_OUT, index=False)
    print(f"✓ Guardado en {RUTA_OUT}  ({os.path.getsize(RUTA_OUT)/1e6:.1f} MB)")
    print(df.head(3).to_string())


if __name__ == "__main__":
    main()
