#!/bin/bash

# Función para verificar si la variable de entorno S3_CRIPT_KEY está configurada
check_s3_cript_key() {
    if [ -z "$S3_CRYPT_KEY" ]; then
        echo "La variable de entorno S3_CRIPT_KEY no está configurada."
        exit 1
    fi
}

# Función para desencriptar el archivo
decrypt_file() {
    local ENCRYPTED_FILE_NAME=$1
    local DECRYPTED_FILE_NAME=$2
    openssl enc -d -aes-256-cbc -in "$ENCRYPTED_FILE_NAME" -out "$DECRYPTED_FILE_NAME" -pass env:S3_CRYPT_KEY
    echo "Archivo desencriptado: $DECRYPTED_FILE_NAME"
}

# Verifica los parámetros
if [ "$#" -ne 2 ]; then
    echo "Uso: $0 nombre-del-archivo-encriptado nombre-del-archivo-desencriptado"
    exit 1
fi

# Verifica la clave de encriptación
check_s3_cript_key

# Parámetros
ENCRYPTED_FILE=$1
DECRYPTED_FILE=$2

# Desencripta el archivo
decrypt_file "$ENCRYPTED_FILE" "$DECRYPTED_FILE"
