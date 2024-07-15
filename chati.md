# Cómo enviar, listar y recuperar datos a Amazon Glacier con la utilidad de línea de comandos aws

Amazon Glacier es un servicio de almacenamiento en la nube de Amazon Web Services (AWS) diseñado para el almacenamiento a largo plazo de datos que son raramente accedidos. Puedes interactuar con Amazon Glacier usando la utilidad de línea de comandos de AWS (AWS CLI). A continuación se detallan los pasos para enviar, listar y recuperar datos de Amazon Glacier utilizando AWS CLI:

### Prerrequisitos

1. **Instalar AWS CLI**: Si aún no tienes AWS CLI instalado, sigue las instrucciones [aquí](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html).

2. **Configurar AWS CLI**: Configura AWS CLI con tus credenciales de AWS ejecutando:
   ```sh
   aws configure
   ```
   Deberás proporcionar tu clave de acceso, clave secreta, región predeterminada y formato de salida.

### Crear un Vault

Un "vault" en Glacier es el contenedor donde almacenarás tus archivos. Para crear un vault:

```sh
aws glacier create-vault --account-id - --vault-name MiVault
```

### Enviar un Archivo a Amazon Glacier

Para subir un archivo a Glacier, primero necesitas calcular el hash SHA256 en árbol (tree hash). AWS CLI proporciona una herramienta para hacerlo.

1. **Calcular el tree hash** (esto puede tardar en archivos grandes):
   ```sh
   aws glacier compute-s3-tree-hash path/al/archivo
   ```

2. **Subir el archivo**:
   ```sh
   aws glacier upload-archive --vault-name MiVault --account-id - --body path/al/archivo
   ```

### Listar Archivos en un Vault

Para listar los archivos en un vault, necesitas iniciar un trabajo de inventario y luego recuperar el resultado del trabajo. El proceso puede tardar varias horas.

1. **Iniciar el trabajo de inventario**:
   ```sh
   aws glacier initiate-job --account-id - --vault-name MiVault --job-parameters '{"Type": "inventory-retrieval"}'
   ```

2. **Listar los trabajos en curso**:
   ```sh
   aws glacier list-jobs --account-id - --vault-name MiVault
   ```

3. **Recuperar el resultado del trabajo** (cuando el trabajo esté completo):
   ```sh
   aws glacier get-job-output --account-id - --vault-name MiVault --job-id ID_DEL_TRABAJO resultado.json
   ```

### Recuperar un Archivo de Amazon Glacier

Para recuperar un archivo, primero necesitas iniciar un trabajo de recuperación y luego descargar el archivo cuando el trabajo esté completo.

1. **Iniciar el trabajo de recuperación**:
   ```sh
   aws glacier initiate-job --account-id - --vault-name MiVault --job-parameters '{"Type": "archive-retrieval", "ArchiveId": "ID_DEL_ARCHIVO"}'
   ```

2. **Listar los trabajos en curso**:
   ```sh
   aws glacier list-jobs --account-id - --vault-name MiVault
   ```

3. **Descargar el archivo** (cuando el trabajo esté completo):
   ```sh
   aws glacier get-job-output --account-id - --vault-name MiVault --job-id ID_DEL_TRABAJO archivo_recuperado
   ```

### Notas Adicionales

- **Tiempo de Procesamiento**: Los trabajos de inventario y recuperación pueden tardar entre varias horas a un día, dependiendo del tamaño y número de archivos.
- **Costos**: Ten en cuenta los costos asociados con el almacenamiento y las solicitudes a Glacier. Consulta la [página de precios de Amazon Glacier](https://aws.amazon.com/glacier/pricing/) para más detalles.

### Recursos
- [Documentación oficial de AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)
- [Documentación de Amazon Glacier](https://docs.aws.amazon.com/amazonglacier/latest/dev/introduction.html)

Con estos comandos, podrás gestionar tus archivos en Amazon Glacier usando la línea de comandos de AWS.


# Cuando pones el parámetro "--acount-id -" ¿Què quieres decir, que hay que sustituir el guión por el número de cuenta o que se utiliza el número de cuenta por defecto?

Cuando se utiliza el parámetro `--account-id -` en los comandos de AWS CLI para Amazon Glacier, el guión (`-`) indica que se debe usar el número de cuenta predeterminado asociado con las credenciales configuradas en tu AWS CLI. No necesitas reemplazar el guión por tu número de cuenta de AWS. AWS CLI automáticamente usa el número de cuenta asociado a las credenciales que has configurado con `aws configure`.

Por lo tanto, cuando ves `--account-id -`, significa que AWS CLI utilizará el número de cuenta predeterminado, y no es necesario que hagas ningún cambio en ese parámetro. Aquí tienes un ejemplo para mayor claridad:

### Ejemplo de Uso

1. **Crear un Vault**:
   ```sh
   aws glacier create-vault --account-id - --vault-name MiVault
   ```

2. **Subir un Archivo**:
   ```sh
   aws glacier upload-archive --vault-name MiVault --account-id - --body path/al/archivo
   ```

3. **Iniciar un Trabajo de Inventario**:
   ```sh
   aws glacier initiate-job --account-id - --vault-name MiVault --job-parameters '{"Type": "inventory-retrieval"}'
   ```

4. **Listar los Trabajos en Curso**:
   ```sh
   aws glacier list-jobs --account-id - --vault-name MiVault
   ```

5. **Recuperar el Resultado de un Trabajo**:
   ```sh
   aws glacier get-job-output --account-id - --vault-name MiVault --job-id ID_DEL_TRABAJO resultado.json
   ```

6. **Iniciar un Trabajo de Recuperación de Archivo**:
   ```sh
   aws glacier initiate-job --account-id - --vault-name MiVault --job-parameters '{"Type": "archive-retrieval", "ArchiveId": "ID_DEL_ARCHIVO"}'
   ```

7. **Descargar un Archivo Recuperado**:
   ```sh
   aws glacier get-job-output --account-id - --vault-name MiVault --job-id ID_DEL_TRABAJO archivo_recuperado
   ```

Usando el guión (`-`) para el `--account-id` simplifica los comandos y permite que AWS CLI maneje automáticamente el número de cuenta, lo cual es especialmente útil cuando se trabaja con múltiples cuentas o roles de IAM.

# El coste del servicio de Amazon Glacier se puede dividir en el coste de subida de datos, el coste de almacenamiento de datos y el coste de recuperación de datos. ¿Podrías explicármelos y calcular para un fichero de 20 GB?

Claro, vamos a desglosar los costos asociados con Amazon Glacier en tres categorías principales: el costo de subida de datos, el costo de almacenamiento de datos y el costo de recuperación de datos. Luego, realizaremos un cálculo estimado para un archivo de 20 GB.

### 1. Coste de Subida de Datos
Amazon Glacier cobra por la transferencia de datos hacia sus servidores.

- **Coste de subida de datos**: La mayoría de las regiones no cobran por la transferencia de datos de subida (ingreso), aunque pueden aplicar cargos en ciertas regiones.
  
Para nuestros cálculos, asumiremos que la subida es gratuita, ya que esta es la política en muchas regiones.

### 2. Coste de Almacenamiento de Datos
Amazon Glacier cobra mensualmente por el almacenamiento de datos.

- **Coste de almacenamiento**: Depende de la región, pero típicamente es alrededor de $0.004 por GB por mes.

Para un archivo de 20 GB:
\[ \text{Coste de almacenamiento} = 20 \text{ GB} \times 0.004 \text{ USD/GB/mes} = 0.08 \text{ USD/mes} \]

### 3. Coste de Recuperación de Datos
Amazon Glacier ofrece diferentes opciones de recuperación de datos con distintos costos y tiempos de recuperación:

- **Standard Retrieval**: Usualmente tarda entre 3 y 5 horas, con un coste de $0.01 por GB.
- **Bulk Retrieval**: Es la opción más económica, puede tardar entre 5 y 12 horas, con un coste de $0.0025 por GB.
- **Expedited Retrieval**: Proporciona acceso en 1 a 5 minutos, con un coste de $0.03 por GB.

Para un archivo de 20 GB, los costes de recuperación serían:

- **Standard Retrieval**:
  \[ \text{Coste de recuperación} = 20 \text{ GB} \times 0.01 \text{ USD/GB} = 0.20 \text{ USD} \]

- **Bulk Retrieval**:
  \[ \text{Coste de recuperación} = 20 \text{ GB} \times 0.0025 \text{ USD/GB} = 0.05 \text{ USD} \]

- **Expedited Retrieval**:
  \[ \text{Coste de recuperación} = 20 \text{ GB} \times 0.03 \text{ USD/GB} = 0.60 \text{ USD} \]

### Resumen de Costos para un Archivo de 20 GB

1. **Coste de subida**: $0 (asumiendo que la transferencia de subida es gratuita)
2. **Coste de almacenamiento**: $0.08 por mes
3. **Coste de recuperación**:
   - Standard Retrieval: $0.20
   - Bulk Retrieval: $0.05
   - Expedited Retrieval: $0.60

### Ejemplo de Cálculo para 1 Mes

Si almacenas un archivo de 20 GB por un mes y luego lo recuperas usando la opción Standard Retrieval:

- **Coste total = Coste de almacenamiento + Coste de recuperación**
- **Coste total = $0.08 + $0.20 = $0.28**

Esto te da una estimación de los costos asociados con el uso de Amazon Glacier para un archivo de 20 GB durante un mes y su posterior recuperación. Ten en cuenta que estos costos pueden variar ligeramente según la región específica y cualquier política de precios actualizada de AWS.

# ¿Cómo podría especificar la clase de almacenamiento glacier que deseo, por ejemplo 'S3 Glacier Instant Retrieval' o 'S3 Glacier Flexible Retrieval' o 'S3 Glacier Deep Archive'?

Para especificar la clase de almacenamiento en Amazon S3, puedes utilizar la opción `--storage-class` al subir archivos a S3. Aquí tienes ejemplos de cómo subir un archivo a diferentes clases de almacenamiento en S3 Glacier utilizando AWS CLI:

### S3 Glacier Instant Retrieval
Para subir un archivo a la clase de almacenamiento `S3 Glacier Instant Retrieval`:
```sh
aws s3 cp path/al/archivo s3://bucket-name/ --storage-class GLACIER_IR
```

### S3 Glacier Flexible Retrieval
Para subir un archivo a la clase de almacenamiento `S3 Glacier Flexible Retrieval` (anteriormente conocido como solo `GLACIER`):
```sh
aws s3 cp path/al/archivo s3://bucket-name/ --storage-class GLACIER
```

### S3 Glacier Deep Archive
Para subir un archivo a la clase de almacenamiento `S3 Glacier Deep Archive`:
```sh
aws s3 cp path/al/archivo s3://bucket-name/ --storage-class DEEP_ARCHIVE
```

### Ejemplo Completo

Suponiendo que tienes un archivo llamado `mi_archivo.txt` y deseas subirlo a un bucket S3 llamado `mi-bucket` en las tres diferentes clases de almacenamiento, los comandos serían:

1. **S3 Glacier Instant Retrieval**:
   ```sh
   aws s3 cp mi_archivo.txt s3://mi-bucket/ --storage-class GLACIER_IR
   ```

2. **S3 Glacier Flexible Retrieval**:
   ```sh
   aws s3 cp mi_archivo.txt s3://mi-bucket/ --storage-class GLACIER
   ```

3. **S3 Glacier Deep Archive**:
   ```sh
   aws s3 cp mi_archivo.txt s3://mi-bucket/ --storage-class DEEP_ARCHIVE
   ```

### Nota Adicional

Al especificar la clase de almacenamiento, asegúrate de que el bucket de destino está configurado correctamente y de que tienes los permisos necesarios para subir archivos. Además, ten en cuenta que el costo y el tiempo de recuperación variarán según la clase de almacenamiento que elijas.

### Costos Asociados

- **S3 Glacier Instant Retrieval**: Proporciona acceso en milisegundos con costos de almacenamiento más altos en comparación con otras opciones de Glacier.
- **S3 Glacier Flexible Retrieval**: Ofrece un balance entre costo y tiempo de recuperación.
- **S3 Glacier Deep Archive**: Es la opción más económica para almacenamiento a largo plazo, pero tiene tiempos de recuperación más largos (puede tomar hasta 12 horas).

Espero que esta información te sea útil. Si tienes alguna otra pregunta o necesitas más detalles, no dudes en preguntar.


# ¿Podrías ponerme un ejemplo completo en el que se cree un recurso s3 y se suba un archivo? ¿Cuál es el límite de tamaño del archivo a subir?

Claro, te proporcionaré un ejemplo completo para crear un bucket S3 y subir un archivo a dicho bucket, especificando la clase de almacenamiento. También mencionaré los límites de tamaño de archivo y cómo manejar archivos grandes.

### Paso 1: Crear un Bucket S3

Primero, crea un bucket S3. Los nombres de los buckets deben ser únicos a nivel mundial.

```sh
aws s3api create-bucket --bucket mi-bucket-ejemplo --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
```

### Paso 2: Subir un Archivo al Bucket con Clase de Almacenamiento Específica

Para subir un archivo, puedes usar `aws s3 cp` o `aws s3api put-object`. Aquí tienes un ejemplo utilizando `aws s3 cp`:

#### Subir un Archivo a S3 Glacier Instant Retrieval

```sh
aws s3 cp path/al/archivo s3://mi-bucket-ejemplo/ --storage-class GLACIER_IR
```

#### Subir un Archivo a S3 Glacier Flexible Retrieval

```sh
aws s3 cp path/al/archivo s3://mi-bucket-ejemplo/ --storage-class GLACIER
```

#### Subir un Archivo a S3 Glacier Deep Archive

```sh
aws s3 cp path/al/archivo s3://mi-bucket-ejemplo/ --storage-class DEEP_ARCHIVE
```

### Límites de Tamaño de Archivo

Amazon S3 tiene ciertos límites de tamaño de archivo:

- **Subida única de archivo (Single PUT)**: El tamaño máximo es de 5 GB.
- **Carga en múltiples partes (Multipart Upload)**: Permite subir archivos de hasta 5 TB.

Para archivos mayores de 5 GB, debes usar Multipart Upload. Aquí tienes un ejemplo para subir un archivo grande utilizando Multipart Upload:

### Subir un Archivo Grande utilizando Multipart Upload

#### Paso 1: Iniciar la Carga Multipart

```sh
aws s3api create-multipart-upload --bucket mi-bucket-ejemplo --key archivo-grande --storage-class GLACIER
```

Esto devolverá un `UploadId` que necesitas para los siguientes pasos.

#### Paso 2: Subir las Partes del Archivo

Divide tu archivo en partes menores de 5 GB cada una y sube cada parte:

```sh
aws s3api upload-part --bucket mi-bucket-ejemplo --key archivo-grande --part-number 1 --body path/al/archivo-parte1 --upload-id <UploadId>
aws s3api upload-part --bucket mi-bucket-ejemplo --key archivo-grande --part-number 2 --body path/al/archivo-parte2 --upload-id <UploadId>
...
```

#### Paso 3: Completar la Carga Multipart

```sh
aws s3api complete-multipart-upload --bucket mi-bucket-ejemplo --key archivo-grande --upload-id <UploadId> --multipart-upload file://etags.json
```

Donde `etags.json` contiene una lista de las partes subidas y sus ETags, algo así:

```json
{
    "Parts": [
        {
            "PartNumber": 1,
            "ETag": "etag1"
        },
        {
            "PartNumber": 2,
            "ETag": "etag2"
        }
    ]
}
```

### Resumen Completo

```sh
# Crear un bucket S3
aws s3api create-bucket --bucket mi-bucket-ejemplo --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2

# Subir un archivo a S3 Glacier Instant Retrieval
aws s3 cp path/al/archivo s3://mi-bucket-ejemplo/ --storage-class GLACIER_IR

# Para archivos grandes (Multipart Upload)
# Paso 1: Iniciar la carga multipart
aws s3api create-multipart-upload --bucket mi-bucket-ejemplo --key archivo-grande --storage-class GLACIER

# Paso 2: Subir las partes del archivo
aws s3api upload-part --bucket mi-bucket-ejemplo --key archivo-grande --part-number 1 --body path/al/archivo-parte1 --upload-id <UploadId>
aws s3api upload-part --bucket mi-bucket-ejemplo --key archivo-grande --part-number 2 --body path/al/archivo-parte2 --upload-id <UploadId>

# Paso 3: Completar la carga multipart
aws s3api complete-multipart-upload --bucket mi-bucket-ejemplo --key archivo-grande --upload-id <UploadId> --multipart-upload file://etags.json
```

Con estos pasos, puedes crear un bucket S3 y subir archivos, incluyendo archivos grandes utilizando Multipart Upload.

# Gracias.  Por favor, créame un bash script que admita dos parámetros, el nombre del bucket y el nombre del archivo:
1.- Si no existe el bucket s3 deseado, lo cree.
2.- Divida el archivo en fragmentos de 100 MB.
3.- Suba, utilizando "multipart upload", las partes del archivo al bucket
4.- Complete la tarea

Claro, a continuación te proporciono un script Bash que cumple con tus requisitos:

```bash
#!/bin/bash

# Verifica que se hayan pasado dos parámetros
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 nombre-del-bucket nombre-del-archivo"
    exit 1
fi

# Parámetros
BUCKET_NAME=$1
FILE_NAME=$2
PART_SIZE=104857600 # 100 MB en bytes

# Crear bucket si no existe
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "Creando bucket $BUCKET_NAME..."
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region us-west-2 --create-bucket-configuration LocationConstraint=us-west-2
fi

# Dividir el archivo en partes de 100 MB
split -b $PART_SIZE -d -a 4 "$FILE_NAME" "$FILE_NAME.part"

# Iniciar la carga multipart
UPLOAD_ID=$(aws s3api create-multipart-upload --bucket "$BUCKET_NAME" --key "$FILE_NAME" --storage-class GLACIER --query 'UploadId' --output text)

# Subir las partes
PART_NUMBER=1
declare -a ETAGS

for PART in "$FILE_NAME".part*; do
    echo "Subiendo parte $PART_NUMBER: $PART"
    ETag=$(aws s3api upload-part --bucket "$BUCKET_NAME" --key "$FILE_NAME" --part-number $PART_NUMBER --body "$PART" --upload-id "$UPLOAD_ID" --query 'ETag' --output text)
    ETAGS+=("{\"PartNumber\": $PART_NUMBER, \"ETag\": $ETag}")
    PART_NUMBER=$((PART_NUMBER + 1))
done

# Completar la carga multipart
ETAGS_JSON=$(printf ",%s" "${ETAGS[@]}")
ETAGS_JSON="[${ETAGS_JSON:1}]"
echo "Completing multipart upload with ETags: $ETAGS_JSON"

aws s3api complete-multipart-upload --bucket "$BUCKET_NAME" --key "$FILE_NAME" --upload-id "$UPLOAD_ID" --multipart-upload "{\"Parts\": $ETAGS_JSON}"

# Limpiar las partes divididas
rm "$FILE_NAME".part*

echo "Carga multipart completada exitosamente."
```

### Descripción del Script

1. **Verificación de Parámetros**: El script verifica que se hayan proporcionado dos parámetros, el nombre del bucket y el nombre del archivo.
2. **Creación del Bucket**: Si el bucket no existe, lo crea.
3. **División del Archivo**: Utiliza el comando `split` para dividir el archivo en partes de 100 MB.
4. **Carga Multipart**:
   - Inicia una carga multipart.
   - Sube cada parte del archivo.
   - Almacena los ETags de cada parte.
5. **Completar la Carga Multipart**: Completa la carga multipart utilizando los ETags almacenados.
6. **Limpieza**: Elimina las partes divididas localmente.

### Ejecución del Script

Guarda el script en un archivo, por ejemplo `upload_to_s3.sh`, y hazlo ejecutable:

```sh
chmod +x upload_to_s3.sh
```

Luego, ejecuta el script proporcionando el nombre del bucket y el nombre del archivo:

```sh
./upload_to_s3.sh nombre-del-bucket nombre-del-archivo
```

Este script manejará la creación del bucket, la división del archivo y la carga multipart de manera automática.

# ¿Cómo sería un script que obtuviese el fichero desde s3?

Claro, te proporcionaré un script Bash que descarga un archivo desde un bucket S3 utilizando Multipart Download si es necesario. Este script verificará la existencia del bucket y el archivo, y luego descargará el archivo en partes si es demasiado grande. Aquí está el script:

```bash
#!/bin/bash

# Verifica que se hayan pasado dos parámetros
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 nombre-del-bucket nombre-del-archivo"
    exit 1
fi

# Parámetros
BUCKET_NAME=$1
FILE_NAME=$2
PART_SIZE=100 # Tamaño de la parte en MB

# Verificar si el bucket existe
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "El bucket $BUCKET_NAME no existe."
    exit 1
fi

# Verificar si el archivo existe en el bucket
if ! aws s3api head-object --bucket "$BUCKET_NAME" --key "$FILE_NAME" 2>/dev/null; then
    echo "El archivo $FILE_NAME no existe en el bucket $BUCKET_NAME."
    exit 1
fi

# Obtener el tamaño del archivo en bytes
FILE_SIZE=$(aws s3api head-object --bucket "$BUCKET_NAME" --key "$FILE_NAME" --query 'ContentLength' --output text)
echo "El tamaño del archivo es: $FILE_SIZE bytes."

# Descargar el archivo en partes si es necesario
if [ "$FILE_SIZE" -le $((PART_SIZE * 1024 * 1024)) ]; then
    echo "Descargando archivo completo..."
    aws s3 cp "s3://$BUCKET_NAME/$FILE_NAME" "$FILE_NAME"
else
    echo "Descargando archivo en partes..."
    PART_NUMBER=1
    BYTE_START=0
    while [ "$BYTE_START" -lt "$FILE_SIZE" ]; do
        BYTE_END=$((BYTE_START + PART_SIZE * 1024 * 1024 - 1))
        if [ "$BYTE_END" -ge "$FILE_SIZE" ]; then
            BYTE_END=$((FILE_SIZE - 1))
        fi
        echo "Descargando parte $PART_NUMBER: bytes $BYTE_START-$BYTE_END"
        aws s3api get-object --bucket "$BUCKET_NAME" --key "$FILE_NAME" --range "bytes=$BYTE_START-$BYTE_END" "$FILE_NAME.part$PART_NUMBER"
        BYTE_START=$((BYTE_END + 1))
        PART_NUMBER=$((PART_NUMBER + 1))
    done

    # Combinar las partes
    echo "Combinando partes..."
    cat "$FILE_NAME".part* > "$FILE_NAME"
    rm "$FILE_NAME".part*
fi

echo "Descarga completada exitosamente."
```

### Descripción del Script

1. **Verificación de Parámetros**: El script verifica que se hayan proporcionado dos parámetros: el nombre del bucket y el nombre del archivo.
2. **Verificación del Bucket**: Comprueba si el bucket existe.
3. **Verificación del Archivo**: Comprueba si el archivo existe en el bucket.
4. **Obtención del Tamaño del Archivo**: Obtiene el tamaño del archivo en bytes.
5. **Descarga del Archivo**:
   - Si el archivo es menor o igual al tamaño de la parte (100 MB en este ejemplo), lo descarga de una sola vez.
   - Si el archivo es mayor, lo descarga en partes utilizando la opción de rango (`--range`) de `aws s3api get-object`.
6. **Combina las Partes**: Une las partes descargadas en un solo archivo y elimina las partes temporales.

### Ejecución del Script

Guarda el script en un archivo, por ejemplo `download_from_s3.sh`, y hazlo ejecutable:

```sh
chmod +x download_from_s3.sh
```

Luego, ejecuta el script proporcionando el nombre del bucket y el nombre del archivo:

```sh
./download_from_s3.sh nombre-del-bucket nombre-del-archivo
```

Este script manejará la descarga del archivo, incluso si es muy grande, dividiéndolo en partes y combinándolas posteriormente.
