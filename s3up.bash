#!/bin/bash

STORAGE_CLASS_REGEX='(STANDARD|INTELLIGENT_TIERING|STANDARD_IA|ONEZONE_IA|GLACIER|GLACIER_IR|DEEP_ARCHIVE|REDUCED_REDUNDANCY)$'

# Verifica que se hayan pasado tres parámetros y que el tipo de almacenamiento es correcto
if [ "$#" -ne 3 ] || [[ ! $3 =~ $STORAGE_CLASS_REGEX ]]; then
    echo "Uso: $0 nombre-del-bucket nombre-del-archivo clase-de-almacenamiento ${STORAGE_CLASS_REGEX}%$"
    exit 1
fi

# Parámetros
BUCKET_NAME=$1
FILE_NAME=$2
STORAGE_CLASS=$3
PART_SIZE=$((100*1024*1024)) # 100 MB en bytes
REGION="us-east-2"
CRYPT_EXTENSION="s3c"

# Crear bucket si no existe
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "Creando bucket $BUCKET_NAME..."
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region $REGION --create-bucket-configuration LocationConstraint="$REGION"
fi

if [ -n $S3_CRYPT_KEY ]
then
    CRYPT_FILE_NAME=${FILE_NAME}.${CRYPT_EXTENSION}
    openssl enc -aes-256-cbc -salt -in "$FILE_NAME" -out "${CRYPT_FILE_NAME}" -pass env:S3_CRYPT_KEY
    FILE_NAME="$CRYPT_FILE_NAME"
fi


FILE_SIZE=$(stat -c %s $FILE_NAME)

if [ "$FILE_SIZE" -le "$PART_SIZE" ]
then
    echo "Subiendo archivo completo..."
    aws s3 cp "$FILE_NAME" "s3://$BUCKET_NAME/$FILE_NAME"
else
    # Dividir el archivo en partes de 100 MB
    split -b $PART_SIZE -d -a 4 "$FILE_NAME" "$FILE_NAME.part"

    # Iniciar la carga multipart
    UPLOAD_ID=$(aws s3api create-multipart-upload --bucket "$BUCKET_NAME" --key "$FILE_NAME" --storage-class $STORAGE_CLASS --query 'UploadId' --output text)

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
fi
