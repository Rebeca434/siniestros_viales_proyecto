"""
main.py
Punto de entrada principal del sistema distribuido de análisis de siniestros viales.

Uso:
    # Flujo completo (generar datos + limpiar + analizar con Ray + benchmark)
    python src/main.py

    # Con datos reales del INEGI (CSV)
    python src/main.py --datos data/tu_archivo.csv

    # Solo análisis Ray (datos ya preparados)
    python src/main.py --datos data/accidentes_limpio.parquet --skip-limpieza

    # Análisis + benchmark de rendimiento
    python src/main.py --benchmark

    # Conectar a Ray Cluster
    python src/main.py --ray-address ray://head:10001
"""
import argparse
import os
import sys
import time
import pandas as pd

# Asegurar que src/ está en el path
sys.path.insert(0, os.path.dirname(__file__))


def parse_args():
    p = argparse.ArgumentParser(description="Análisis distribuido de siniestros viales")
    p.add_argument("--datos",         default=None,
                   help="Ruta al archivo de datos (CSV o Parquet)")
    p.add_argument("--skip-limpieza", action="store_true",
                   help="Omitir limpieza si los datos ya están preparados")
    p.add_argument("--benchmark",     action="store_true",
                   help="Ejecutar comparación Pandas vs Ray")
    p.add_argument("--ray-address",   default=None,
                   help="Dirección del Ray Cluster (ej: ray://head:10001)")
    p.add_argument("--n-particiones", type=int, default=None,
                   help="Número de particiones Ray (default = CPUs)")
    return p.parse_args()


def banner(msg: str):
    linea = "─" * 60
    print(f"\n{linea}\n  {msg}\n{linea}")


def main():
    args = parse_args()
    t_inicio = time.time()

    os.makedirs("data",    exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    # ══ PASO 1 — Obtener datos ═════════════════════════════════════════════════
    banner("PASO 1 — Preparación de datos")

    ruta_raw    = args.datos or "data/accidentes_atus.parquet"
    ruta_limpio = "data/accidentes_limpio.parquet"

    if not os.path.exists(ruta_raw):
        print("  No se encontró el archivo de datos. Generando dataset sintético…")
        from generar_datos import main as gen_main
        gen_main()
    else:
        print(f"  Usando datos: {ruta_raw}")

    # ══ PASO 2 — Limpieza ══════════════════════════════════════════════════════
    if not args.skip_limpieza or not os.path.exists(ruta_limpio):
        banner("PASO 2 — Limpieza y normalización")
        from limpieza import pipeline as limpiar
        limpiar(ruta_raw, ruta_limpio)
    else:
        banner("PASO 2 — Limpieza omitida (--skip-limpieza)")
        print(f"  Usando datos limpios: {ruta_limpio}")

    df = pd.read_parquet(ruta_limpio)
    print(f"  Dataset listo: {len(df):,} registros")

    # ══ PASO 3 — Análisis con Ray ══════════════════════════════════════════════
    banner("PASO 3 — Análisis distribuido con Ray")
    from analisis_ray import analizar_ray, guardar_resultados as guardar_ray
    import ray

    resultados_ray, t_ray = analizar_ray(
        df,
        n_particiones=args.n_particiones,
        address=args.ray_address,
    )
    guardar_ray(resultados_ray, "outputs/ray")

    if ray.is_initialized():
        ray.shutdown()

    # ══ PASO 4 — Análisis secuencial (siempre, para tener los CSVs) ════════════
    banner("PASO 4 — Análisis secuencial (Pandas)")
    from analisis_secuencial import analizar as analizar_seq, guardar_resultados as guardar_seq

    resultados_seq, t_seq = analizar_seq(df)
    guardar_seq(resultados_seq, "outputs/secuencial")

    # ══ PASO 5 — Benchmark ════════════════════════════════════════════════════
    if args.benchmark:
        banner("PASO 5 — Benchmark de rendimiento")
        from benchmark import ejecutar_benchmark
        bm = ejecutar_benchmark(
            ruta_datos=ruta_limpio,
            ray_address=args.ray_address,
        )

    # ══ RESUMEN FINAL ══════════════════════════════════════════════════════════
    banner("✓ PROCESO COMPLETADO")
    print(f"  Registros analizados : {len(df):,}")
    print(f"  Tiempo Ray           : {t_ray:.3f}s")
    print(f"  Tiempo Secuencial    : {t_seq:.3f}s")
    if t_seq > 0:
        print(f"  Speedup (local)      : {t_seq/t_ray:.2f}×")
    print(f"  Tiempo total         : {time.time()-t_inicio:.2f}s")
    print()
    print("  Resultados en:  outputs/ray/  y  outputs/secuencial/")
    print("  Dashboard:      streamlit run src/dashboard.py")
    print()


if __name__ == "__main__":
    main()
