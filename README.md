# Siniestros Viales con Ray
Sistema distribuido para análisis de accidentes viales en México usando datos abiertos del INEGI (ATUS), Python y Ray.

# Tecnologías
Python 3.11 · Ray 2.10 · Pandas · PyArrow · Streamlit · Plotly · Docker

# Ejecución
Local (paralelo):

bashpip install -r requirements.txt

python src/main.py --benchmark

streamlit run src/dashboard.py

Cluster con Docker (distribuido):

bashcd docker && docker compose up --build

Ray Dashboard  → http://localhost:8265

Streamlit      → http://localhost:8501

# Datos
Descarga el CSV de ATUS en https://www.inegi.org.mx/programas/accidentes/ y colócalo en data/. Sin el archivo, el sistema genera un dataset sintético de 500K registros automáticamente.
bashpython src/main.py --datos data/tu_archivo.csv --benchmark

# Resultados
Los análisis se guardan en outputs/ray/ y outputs/secuencial/. El benchmark compara tiempos y speedup entre Pandas, Ray local y Ray Cluster.

# Integrantes
Manuel Martinez Martinez 368064

Rebeca Portillo Saenzpardo 368094

Pablo Gael Torres 368073

Fernando Grijalva Fernández 367634
