from util import logcfg
import logging
import datetime
import os
import boto3
from botocore.exceptions import ClientError


PART_SIZE = 100 * 1024 * 1024  # 100 MB en bytes
DEFAULT_REGION = 'us-east-2'
DEFAULT_STORAGE_CLASS='STANDARD'
S3_AWS_SERVICE = 's3'

class S3Ops():
    @staticmethod
    def split_file(fname, part_size):
        fname_path, fname_base = os.path.split(fname)
        part_number = 0
        parts = []

        with open(fname, 'rb') as file:
            while True:
                part_data = file.read(part_size)
                if not part_data:
                    break

                part_base_file_name = f"{fname_base}.part{part_number:04d}"
                part_file_name = os.path.join(fname_path, part_base_file_name)
                with open(part_file_name, 'wb') as part_file:
                    part_file.write(part_data)

                part_number += 1
                print(f"Parte {part_number} creada: {part_file_name}")
                parts.append(part_file_name)
        return parts

    def __init__(self, 
                 region = DEFAULT_REGION, 
                 storage_class = DEFAULT_STORAGE_CLASS):
        self.region = region
        self.client = boto3.client(S3_AWS_SERVICE, region)
        self.resource = boto3.resource(S3_AWS_SERVICE)
        self.storage_class = storage_class

    def list_buckets(self):
        response = self.client.list_buckets()
        return [bucket['Name'] for bucket in response['Buckets']]
    
    def list_files(self, bucket):
        response = self.client.list_objects_v2(Bucket=bucket)
        if 'Contents' not in response:
            return []
        else:
            return [obj['Key'] for obj in response['Contents']]

    def exists_bucket(self, bucket):
        return bucket in self.list_buckets()
    
    def create_bucket(self, bucket):
        logging.info(f"Creando bucket {bucket}")
        self.client.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint': self.region})
        logging.info(f"Bucket {bucket} creado")

    def upload_file_to_bucket(self, bucket, fname, storage_class=DEFAULT_STORAGE_CLASS):
        logging.info(f"Subiendo archivo {fname} a bucket {bucket}")
        file_size = os.path.getsize(fname)
        if file_size <= PART_SIZE:
            logging.info("Subiendo archivo completo...")
            self.client.upload_file(fname, 
                                    bucket, 
                                    fname, 
                                    ExtraArgs={'StorageClass': storage_class})
        else:
            parts = self.split_file(fname, PART_SIZE)
            # Dividir el archivo en partes de 100 MB

            # Iniciar la carga multipart
            multipart_upload = self.client.create_multipart_upload(Bucket=bucket, Key=fname, StorageClass=self.storage_class)
            upload_id = multipart_upload['UploadId']

            # Subir las partes
            part_number = 1
            etags = []
            
            for part in parts:
                logging.info(f"Subiendo parte {part_number}: {part}")
                with open(part, 'rb') as data:
                    response = self.client.upload_part(
                        Bucket=bucket,
                        Key=fname,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=data
                    )
                etags.append({'PartNumber': part_number, 'ETag': response['ETag']})
                part_number += 1

            # Completar la carga multipart
            self.client.complete_multipart_upload(
                Bucket=bucket,
                Key=fname,
                UploadId=upload_id,
                MultipartUpload={'Parts': etags}
            )

            # Limpiar las partes divididas
            for part in parts:
                os.remove(part)

            logging.info("Carga multipart completada exitosamente.")
    
    def download_file_from_bucket(self, bucket, fname, dest_fname):
        if not self.exists_bucket(bucket):
            raise ClientError(f"No existe bucket {bucket}")

        response = self.client.head_object(Bucket=bucket, Key=fname)
        
        # Obtener el tamaño del archivo en bytes
        file_size = response['ContentLength']
        logging.info(f"El tamaño del archivo es: {file_size} bytes.")

        # Descargar el archivo en partes si es necesario
        if file_size <= PART_SIZE:
            logging.info("Descargando archivo completo...")
            self.client.download_file(bucket, fname, fname)
        else:
            print("Descargando archivo en partes...")
            part_number = 1
            byte_start = 0

            while byte_start < file_size:
                byte_end = byte_start + PART_SIZE - 1
                if byte_end >= file_size:
                    byte_end = file_size - 1

                part_file_name = f"{dest_fname}.part{part_number:04d}"
                print(f"Descargando parte {part_number}: bytes {byte_start}-{byte_end}")
                with open(part_file_name, 'wb') as part_file:
                    response = self.client.get_object(Bucket=bucket, 
                                           Key=fname, 
                                           Range=f"bytes={byte_start}-{byte_end}")
                    part_file.write(response['Body'].read())

                byte_start = byte_end + 1
                part_number += 1

            # Combinar las partes
            logging.info("Combinando partes...")
            with open(dest_fname, 'wb') as final_file:
                for i in range(1, part_number):
                    part_file_name = f"{dest_fname}.part{i:04d}"
                    with open(part_file_name, 'rb') as part_file:
                        final_file.write(part_file.read())
                    os.remove(part_file_name)

        logging.info("Descarga completada exitosamente.")
        
    def delete_file(self, bucket, fname):
        if not self.exists_bucket(bucket):
            raise ClientError(f"No existe bucket {bucket}")
        logging.info(f"Borrando fichero {fname} de bucket {bucket}")
        try:
            self.client.delete_object(Bucket=bucket, Key=fname)
            logging.info(f"Fichero {fname} borrado de bucket {bucket}")
        except ClientError as e:
            logging.error(f"Error al borrar el fichero {fname} del bucket {bucket}: {e}")
            raise

    def delete_bucket(self, bucket):
        if not self.exists_bucket(bucket):
            raise ClientError(f"No existe bucket {bucket}")
        bucket_resource = self.resource.Bucket(bucket)
        try:
            bucket_resource.objects.all().delete()
            logging.info(f"Objetos del bucket {bucket} borrados")
            bucket_resource.delete()
            logging.info(f"Bucket {bucket} borrado")
        except ClientError as e:
            logging.error(f"Error al borrar el bucket {bucket}: {e}")
            raise
        
def main():
    pass

if __name__ == "__main__":
    logcfg(__file__)

    stime = datetime.datetime.now()
    main()
    etime = datetime.datetime.now()
    logging.info(f"Ejecución del programa ha tardado {etime - stime}")
    exit(0)
