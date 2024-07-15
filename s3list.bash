#!/bin/bash

# Función para listar todos los buckets
list_buckets() {
    echo $(aws s3api list-buckets --query 'Buckets[].Name' --output text)
}

# Función para listar el contenido de un bucket
list_bucket_contents() {
    local BUCKET_NAME=$1
    echo $(aws s3 ls "s3://$BUCKET_NAME/")
}

# Función para listar recursivamente el contenido de todos los buckets
list_all_buckets_contents() {
    for BUCKET in $(list_buckets)
    do
        echo "Contenido del bucket $BUCKET:"
        list_bucket_contents ${BUCKET}
    done
}

# Verifica los parámetros
if [ "$#" -eq 0 ]; then
    list_buckets
elif [ "$#" -eq 1 ]; then
    if [ "$1" == "--recursive" ]; then
        echo "Contenido de todos los buckets"
        list_all_buckets_contents
    else
        echo "Contenido de $1"
        list_bucket_contents "$1"
    fi
else
    echo "Uso: $0 [--recursive] [nombre-del-bucket]"
    exit 1
fi
