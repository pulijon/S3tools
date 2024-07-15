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
