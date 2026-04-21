# Instructivo para ejecutar el proyecto: Challenge — Data engineer (Mid Level)

## 🧩 Descripción general

Este proyecto implementa un pipeline de datos completo utilizando:

- **Airflow** → Orquestación del pipeline ETL  
- **Python (ETL)** → Extracción, transformación y carga  
- **PostgreSQL** → Almacenamiento  
- **Django** → Backend + UI de monitoreo (tipo CETCIN)  
- **Docker** → Infraestructura reproducible  

---

## 🚀 Etapas del proyecto

1. Construcción de infraestructura (Docker)
2. Ejecución del pipeline de datos (Airflow)
3. Monitoreo del pipeline (Django UI)

---

## 📁 Estructura del proyecto

```
├── airflow/
│   ├── dags/
│   │   └── etl_pipeline_dag.py
│   ├── logs/
│   └── plugins/
├── code/
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── extract.py
│   │   ├── transform.py
│   │   └── load.py
│   ├── __init__.py
│   ├── api.py
│   └── source/
│       └── events.json
├── data/
├── .env
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## ⚠️ Notas de versionado

- `.env` **sí está versionado** (solo para fines de prueba, sin datos sensibles)
- `data/` **NO se versiona** (volumen de PostgreSQL)

---


## 🐳 1. Construcción de infraestructura

### 🔹 Levantar el entorno

```bash
docker compose down
(opcional, borrado fuerte (excepto las carpetas locales)) docker compose down -v --remove-orphans
docker compose build --no-cache
sudo rm -rf data
docker compose up db -d
docker compose run airflow-init
docker compose up --scale airflow-worker=3 -d
(si borraste la DB, entonces:
    docker exec -it django-backend bash
    python manage.py migrate
    python manage.py createsuperuser
)
```

---



### 🧠 Arquitectura

Cada componente corre en su propio contenedor:

- `db` → PostgreSQL  
- `etl` → lógica Python  
- `airflow-*` → orquestación  
- `django-backend` → UI + API  

---

## 🧱 2. Configuración de Django

### 🔹 Crear proyecto (solo la primera vez)

```bash
docker compose run --rm django-backend bash
```

Dentro del contenedor:

```bash
django-admin startproject config .
exit
```

Reconstruir imagen:

```bash
docker compose build django-backend
docker compose up django-backend -d
```

---

## 🧩 3. Crear app de monitoreo

```bash
docker compose exec django-backend python manage.py startapp monitor
```

---

### 🔹 Registrar app

En `config/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'monitor',
]
```

---

### 🔹 Vista básica

`monitor/views.py`

```python
from django.http import HttpResponse

def home(request):
    return HttpResponse("Monitor ETL funcionando 🚀")
```

---

### 🔹 URLs

`monitor/urls.py`

```python
from django.urls import path
from .views import home

urlpatterns = [
    path('', home),
]
```

`config/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitor.urls')),
]
```

---

## 🗄️ 4. Conexión a PostgreSQL

En `config/settings.py`:

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '5432',
        'OPTIONS': {
            'options': f"-c search_path={os.getenv('DB_SCHEMA')}"
        }
    }
}
```

---

### 🔹 Migraciones

```bash
docker compose exec django-backend python manage.py migrate
```

---

## 🌐 5. Probar aplicación

```bash
docker compose restart django-backend
```

Abrir en navegador:

```
http://localhost:8000
```

---

## 📊 6. Modelo de monitoreo

Ejemplo: `PipelineRun`

Después de definir modelos:

```bash
docker compose exec django-backend python manage.py makemigrations
docker compose exec django-backend python manage.py migrate
```

---

### 🔹 Admin Django

`monitor/admin.py`

```python
from django.contrib import admin
from .models import PipelineRun

admin.site.register(PipelineRun)
```

Crear superusuario:

```bash
docker compose exec django-backend python manage.py createsuperuser
```

appuser
123f

---

## 🖥️ 7. UI tipo dashboard (CETCIN básico)

Crear template:

```
monitor/templates/monitor/dashboard.html
```

Actualizar vista para usar HTML.

---

## 🔁 8. Levantar servicios

```bash
docker compose up -d
```

👉 Esto **NO recrea el proyecto**, solo levanta contenedores existentes.

---

## 🧠 Notas importantes

- Airflow maneja ejecución del pipeline  
- Django actúa como:
  - UI de monitoreo
  - Control manual de ejecuciones  
- PostgreSQL usa múltiples schemas:
  - `airflow`
  - `analytics`
  - `backend` (Django)

---


ejecutar el dag desde consola (ejecutar airflow con su API)
curl -X POST "http://localhost:8080/api/v1/dags/etl_pipeline/dagRuns" \
  -u "airflow:airflow" \
  -H "Content-Type: application/json" \
  -d '{}'







## 2. Ejecutar airflow desde el sitio web

http://localhost:8080


## 2. Ejecutar pipeline de datos

Para realizar la ejecución del 'ETL pipeline' entre al contenedor de python (pyback) y ejecute el programa main.py
:w

```
(entrar al contenedor)
docker exex -it pyback bash

(una vez dentro del contenedor:)
python main.py
```

### Decisiones y explicación del diseño del ETL pipeline 

Para mantener legilibilidad en el diseño del código se optó por una arquitectura modular. La función orquestadora es 'main', la cual, ejecuta los siguientes procesos de forma secuencial:

- Conexión a la base de datos (Postgresql)
- Ingesta de la información
- Pre-visualización de información
- Transformación y normalización de la información
- Carga de la información

#### Ingesta de la información
Se decidió trabajar con 'pandas' por la claridad en código y versatilidad que éste ofrece al proceso. Además, debido a que es un entorno de prueba (con una ingesta de datos relativamente pequeña) no es necesario utilizar el 'poder' de un gestor de bases de datos formal (Postgres, o servicios de nube como BigQuery o GCS) para la parte de transformación de la información.

#### Transformación de la información

La parte de validación del reto mencionaba que se filtrara para eliminar registros con 'user_id' faltante, o vacío. Así, se consideraron como válidos los siguientes tipos de  user_id's: 

- números
- letras
- caracteres de puntuación o especiales (#, $, %, ...)
- cualquier combinación de las anteriores

Nota: en caso que se desee restringir más la 'validez' del campo 'user_id' deberá modificarse el filtrado realizado en la parte del código: 'Stage: user_id faltante o vacío'

Para la parte de validación de teléfonos se han considerado como válidos números telefónicos con 10 o 12 dígitos. En esta parte se ha dado la flesibilidad que un valor de 'phone' con letras o caracteres sea valido siempre y cuando tenga 10 0 12 dígitos; esto permite incluir como válidos valores como:

- '+52 1234567890'
- '1 2 3 4 5 6 7 8 9 0'
- '1-2-3-4-5-6-7-8-9-0'
- 'clave: 52, tel: 1234567890'
- ...

#### Normalización de la información

Esta etapa consideraba normas como:
- cadenas de texto en minúsculas
- restricción de dominio
- añadir valores por defecto

La gran mayoría de los campos involucrados se encuentran anidados en el Json fuente, por ello, la estrategía más intuitiva a seguir sería ciclar por cada registro de origen y aplicar las correspondientes normas. Sin embargo, ello puede conllevar a generar un proceso computacionalmente costo (principalmente en tiempo). Así, se ha decidió extraer los campos involucrados y colocarlos columnas 'nuevas' del pandas DataFrame. Este enfoque tiene la contraparte negativa de aumentar la carga en memoria (RAM, o en disco si la ingesta es muy grande), pero reduce en gran medida el tiempo de computo al realizar el proceso 'en una sola pasada' (por toda la columna). Nota: Si la ingesta es muy grande, del orden de Gigas o Teras, podría optarse por utilizar pySpark para distribuir el proceso (bajar la carga a memoria) y mantenerlo en tiempos de ejecución tolerables.


#### Generación de la tabla diaria

La parte final del proceso de transformación entrega la tabla diaria solicitada por el desafio (df_table). La parte clave de este proceso es el filtrado que se ha realizado, por usuario y por fecha, aprovechando la versatilidad de pandas antes mencionado (df_data.groupby).

#### Carga de la información

El proceso ETL finaliza con la carga de la información a una tabla en Postgresql (metrics_daily). Aquí, para simplificar el proceso, se ha decidido re-escribir la tabla cada que se ejecuta el programa. Sin embargo, podría mejorarse esta parte del proceso realizando:

- Validaciones previas antes de 'escribir' información
- Automatizando procesos de borrado o re-ejecución del proceso
- Realizar la carga como un proceso incremental, no como un proceso 'truncate'

Nota: respecto al último punto, en situaciones reales (producción) con ingestas considerables o ejecutadas frecuentemente (programadas varias veces al día), es indispensable diseñar la carga de forma incremental (no 'truncate'), pues esto reduce considerablemente los tiempos de ejecución y el consumo de recursos.

## 3. Consulta API: FastAPI

Para esta etapa se utilizó 'FastAPI' para exponer un endpoint REST que permite consultar las métricas almacenadas en la base de datos. Se eligió por su simplicidad, alto rendimiento y facilidad de integración con Python.

El endpoint disponible es:

GET /daily_stats?date=YYYY-MM-DD

Este endpoint recibe una fecha como parámetro y retorna las métricas agregadas correspondientes (usuarios, búsquedas, compras y monto total).

Uso

Con el servicio activo (el proyecto docker activo), se puede consultar desde navegador o curl:

```
http://localhost:8000/daily_stats?date=2025-01-15
```

La API consulta directamente la tabla metrics_daily en PostgreSQL y devuelve la información en formato JSON; ejemplo.

```
{"date":"2025-01-15","total_users":3,"total_searches":3,"total_purchases":2,"total_purchased_amount":2100.0}
```

