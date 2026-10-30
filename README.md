# App de Diseño Experimental

Aplicación educativa multipágina desarrollada con Python y Streamlit para el
curso de Diseño Experimental del programa de Ingeniería Agrícola de la
Universidad de Sucre. Permite explorar diseños experimentales y apoyar el
análisis e interpretación de ensayos agrícolas; el estudiante debe revisar los
supuestos y verificar los resultados.

## Módulos

| Módulo | Estado | Descripción |
|---|---|---|
| DCA — Diseño completamente al azar | Disponible | Analiza un factor en unidades experimentales homogéneas; incluye el ejemplo de humedad de yuca con cuatro secadores solares. |
| DBCA — Diseño en bloques completos al azar | En construcción | Controla una fuente conocida de variación mediante bloques. |
| DCL — Diseño en cuadrado latino | En construcción | Controla dos fuentes de variación mediante filas y columnas. |
| DPD — Diseño de parcelas divididas | En construcción | Organiza factores en parcelas principales y subparcelas. |
| Factoriales | En construcción | Estudia varios factores y sus interacciones. |
| RSM — Metodología de superficie de respuesta | En construcción | Modela y explora respuestas según factores cuantitativos. |

## Estructura del proyecto

```text
.
├── app.py                  # Portada de la aplicación
├── pages/                  # Una página Streamlit por diseño experimental
├── utils/                  # Funciones reutilizables para análisis y diagnóstico
├── data/                   # Datos CSV de ejemplo
├── verificacion/           # Scripts de R para verificar los análisis
└── requirements.txt        # Dependencias de Python
```

## Instalación y ejecución

### VS Code local en Windows

Desde PowerShell, en la carpeta del proyecto, crea y activa un entorno virtual,
instala las dependencias e inicia Streamlit:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

### GitHub Codespaces

En la terminal del Codespace, desde la carpeta del proyecto, instala las
dependencias y ejecuta la aplicación:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit mostrará la dirección local de la aplicación y, en Codespaces,
permitirá abrir el puerto correspondiente en el navegador.

## Verificación con R

El script `verificacion/verificacion_dca.R` realiza un análisis independiente
del DCA. Para ejecutarlo, coloca el archivo `dca_mi_variante.csv` en `data/` y
ejecuta el script desde la carpeta `verificacion/`:

```bash
Rscript verificacion_dca.R
```

El CSV debe contener las columnas `secador` y `humedad`.

## Autor

Oscar De hoyos — estudiante del curso de Diseño Experimental, semestre 2026-2,
Ingeniería Agrícola, Universidad de Sucre.

## Uso de inteligencia artificial

Se utilizó inteligencia artificial como apoyo para crear y revisar partes de
la aplicación, documentación y código de verificación. El autor revisa los
cambios; los resultados estadísticos proceden de los datos analizados y deben
ser interpretados y verificados por el estudiante.
