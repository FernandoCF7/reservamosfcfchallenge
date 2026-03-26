# Instructivo para ejecutar el proyecto: Challenge — Data engineer (Mid Level)

## Descripción general

El presente documento contiene las instrucciones para generar la infraestructura (Docker) y ejecutar el proceso para cumplir el 'Challenge — Data engineer (Mid Level)'

### Etapas:
- Construir la infraestructura
- Ejecutar pipeline de datos
- Consulta API: FastAPI

### Estructura del proyecto:
```
.
├── code/
│   ├── main.py          # ETL pipeline
│   ├── api.py           # REST API
│   ├── source/
|   |   └── events.json  # Input data 
│   |── requirements.txt
│   └── Dockerfile
├── data/
│   └── ...              # Posstgresql data 
├── .env
├── compose.yml          # Docker compose
├── README.md
└── prompts_AI_usados.txt
```

## 1. Construir la infraestructura

### Notas relacionadas al versionado

Warnign: Se ha decidido no incluir el archivo .env en el archivo .gitignore, pese a que esto en un entorno 'productivo' nunca debe realizarse. Sin embargo, y considerando que no se está manejando información sensible, se tomó está decición para mantener el proceso de creación de infraestructura y ejecución del proceso lo más transarente y directo al usuario.

Se ha decidido no incluir al repositorio la ruta ./data debido a que es el volumen donde se monto la base de datos (Postgres), ello conllevaría a tener un reposositorio inecesariamente grande.

### Infraestructura con Docker

La infraestructura del proyecto se construye con Docker (docker-compose).

Nota: Para mantener la escalabilidad se optó por utilizar contenedores individuales para la lógica (python-backen) y la base de datos (Postgresql) del sistema. Por otra parte, se decició 'montar' volumenes para el backend y base de datos, para preservar el acceso y gobernanza del proceso y de la información.

Ejecute la siguiente sentencia en el directorio raíz del proyecto para 'levantar' su infraestructura

```
docker compose -p reservamos up -d 

```

Nota: en este caso el proyecto se ha nombrado 'reservamos'. Puede cambiar dicho nombre sí así lo desea, en cuyo caso la sentencia quedaría así:



```
docker compose -p nombreDelContenedor up -d 

```

Nota: para la parte del contenedor python (pyback) el archivo compose toma en cuenta la creación automática de los módulos que el programa necesita (ejecuta en automático el archivo 'requirements.txt'; así, no es necesario realizar configuración alguna)



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

