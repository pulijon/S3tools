#!/bin/bash

# Función para verificar si un bucket existe
bucket_exists() {
    local BUCKET_NAME=$1
    aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null
}

# Función para verificar si un objeto existe en un bucket
object_exists() {
    local BUCKET_NAME=$1
    local OBJECT_KEY=$2
    aws s3api head-object --bucket "$BUCKET_NAME" --key "$OBJECT_KEY" 2>/dev/null
}

# Función para borrar un bucket
delete_bucket() {
    local BUCKET_NAME=$1
    echo "Eliminando bucket $BUCKET_NAME..."
    aws s3 rb "s3://$BUCKET_NAME" --force
    echo "Bucket $BUCKET_NAME eliminado."
}

# Función para borrar un objeto en un bucket
delete_object() {
    local BUCKET_NAME=$1
    local OBJECT_KEY=$2
    echo "Eliminando objeto $OBJECT_KEY en bucket $BUCKET_NAME..."
    aws s3 rm "s3://$BUCKET_NAME/$OBJECT_KEY"
    echo "Objeto $OBJECT_KEY eliminado del bucket $BUCKET_NAME."
}

# Verifica los parámetros
if [ "$#" -eq 1 ]; then
    BUCKET_NAME=$1
    if bucket_exists "$BUCKET_NAME"; then
        delete_bucket "$BUCKET_NAME"
    else
        echo "El bucket $BUCKET_NAME no existe."
    fi
elif [ "$#" -eq 2 ]; then
    BUCKET_NAME=$1
    OBJECT_KEY=$2
    if object_exists "$BUCKET_NAME" "$OBJECT_KEY"; then
        delete_object "$BUCKET_NAME" "$OBJECT_KEY"
    else
        echo "El objeto $OBJECT_KEY no existe en el bucket $BUCKET_NAME."
    fi
else
    echo "Uso: $0 nombre-del-bucket [nombre-del-objeto]"
    exit 1
fi
