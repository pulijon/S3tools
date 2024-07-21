from threading import Thread
import tkinter as tk
from tkinter import ttk
import logging
import boto3
from botocore.exceptions import ClientError
import os
import math
import time

PART_SIZE = 10 * 1024 * 1024  # 100 MB en bytes
DEFAULT_REGION = 'us-east-2'
DEFAULT_STORAGE_CLASS='STANDARD'
S3_AWS_SERVICE = 's3'
CRYPT_EXTENSION = ".s3enc"
DECRYPT_EXTENSION = ".s3dec"

class S3job(Thread):
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
                logging.debug(f"Parte {part_number} creada: {part_file_name}")
                parts.append(part_file_name)
        return parts

    def __init__(self,
                 idjob, 
                 jobtype,
                 jobq,
                 root=None,
                 bucket=None,
                 bucket_file="",
                 local_file="",
                 storage_class="DEFAULT_STORAGE_CLASS",
                 region=DEFAULT_REGION,
                 encrypted=False,
                 crypt=None):
        super().__init__()
        self.idjob = idjob
        self.jobtype = jobtype
        self.jobq = jobq
        self.root = root
        self.bucket = bucket
        self.bucket_file = bucket_file
        self.local_file = local_file
        self.storage_class = storage_class
        self.region = region
        self.encrypted = encrypted
        self.crypt = crypt
        self.ops = {
            'list_buckets': self.list_buckets,
            'list_files': self.list_files,
            'upload': self.upload,
            'download': self.download,
            'delete_file': self.delete_file,
            'create_bucket': self.create_bucket,
            'delete_bucket': self.delete_bucket
        }
    
    def list_buckets(self):
        response = self.client.list_buckets()
        list = [bucket['Name'] for bucket in response['Buckets']]
        self.jobq.put((self.idjob,
                  'completed',
                  list))
    
    def list_files(self):
        response = self.client.list_objects_v2(Bucket=self.bucket)
        contents = response.get('Contents', [])
        list = [obj['Key'] for obj in contents]
        self.jobq.put((self.idjob,
                  'completed',
                  list))

    def progress_bar_create(self, label_text, maximum):
        progress_frame = tk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        label = tk.Label(progress_frame, text=label_text)
        label.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        bar = ttk.Progressbar(progress_frame, 
                              orient=tk.HORIZONTAL, 
                              length=400, 
                              mode='determinate',
                              maximum=maximum,
                              value=0)
        bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        self.progress_elements = {
            'frame': progress_frame,
            'label': label,
            'bar': bar
        }

    def progress_bar_destroy(self):
        time.sleep(3)
        if self.progress_elements:
            self.progress_elements['bar'].destroy()
            self.progress_elements['label'].destroy()
            self.progress_elements['frame'].destroy()
            self.progress_elements = {}

    def progress_bar_step(self, steps=1):
        if self.progress_elements:
            self.progress_elements['bar']['value']+= steps
            logging.debug(f"Valor de barra: {self.progress_elements['bar']['value']}")
            self.root.update_idletasks()

    def upload(self):
        bucket = self.bucket
        local_file = self.local_file
        storage_class = self.storage_class

        if self.encrypted:
            self.bucket_file = f'{self.local_file}{CRYPT_EXTENSION}'
            self.crypt.encrypt_file(local_file, self.bucket_file)
            fname = self.bucket_file
        else:
            fname = local_file
            self.bucket_file = fname

        logging.info(f"Subiendo archivo {fname} a bucket {bucket}")
        file_size = os.path.getsize(fname)
        if file_size <= PART_SIZE:
            logging.info("Subiendo archivo completo...")
            self.client.upload_file(fname, 
                                    bucket, 
                                    self.bucket_file, 
                                    ExtraArgs={'StorageClass': storage_class})
        else:
            parts = self.split_file(fname, PART_SIZE)
            # Dividir el archivo en partes de 100 MB

            # Iniciar la carga multipart
            multipart_upload = self.client.create_multipart_upload(Bucket=bucket, Key=fname, StorageClass=self.storage_class)
            upload_id = multipart_upload['UploadId']
            
            self.progress_bar_create(f'Subiendo - bucket: {bucket} - fichero: {fname}', len(parts))

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
                self.progress_bar_step()

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
            self.progress_bar_destroy()
            logging.info("Carga multipart completada exitosamente.")

        self.jobq.put((self.idjob,
                 'completed',
                 None))

    def download(self):
        bucket = self.bucket
        bucket_file = self.bucket_file
        response = self.client.head_object(Bucket=bucket, Key=bucket_file)
        local_file = self.local_file
        
        # Obtener el tamaño del archivo en bytes
        file_size = response['ContentLength']
        logging.info(f"El tamaño del archivo es: {file_size} bytes.")

        # Descargar el archivo en partes si es necesario
        if file_size <= PART_SIZE:
            logging.info("Descargando archivo completo...")
            self.client.download_file(bucket, bucket_file, local_file)
        else:
            logging.info("Descargando archivo en partes...")
            part_number = 1
            byte_start = 0
            nparts = math.ceil(file_size / PART_SIZE)
            
            self.progress_bar_create(f'Descargando - bucket: {bucket} - fichero: {bucket_file}', nparts)


            while byte_start < file_size:
                byte_end = byte_start + PART_SIZE - 1
                if byte_end >= file_size:
                    byte_end = file_size - 1

                part_file_name = f"{local_file}.part{part_number:04d}"
                logging.debug(f"Descargando parte {part_number}: bytes {byte_start}-{byte_end}")
                with open(part_file_name, 'wb') as part_file:
                    response = self.client.get_object(Bucket=bucket, 
                                           Key=bucket_file, 
                                           Range=f"bytes={byte_start}-{byte_end}")
                    part_file.write(response['Body'].read())

                byte_start = byte_end + 1
                self.progress_bar_step()
                part_number += 1

            # Combinar las partes
            logging.info("Combinando partes...")
            with open(local_file, 'wb') as final_file:
                for i in range(1, part_number):
                    part_file_name = f"{local_file}.part{i:04d}"
                    with open(part_file_name, 'rb') as part_file:
                        final_file.write(part_file.read())
                    os.remove(part_file_name)
            self.progress_bar_destroy()
            
        if self.encrypted:
            dest_root, dest_ext = os.path.splitext(self.local_file)
            output_file_path = dest_root if dest_ext == CRYPT_EXTENSION else f'{local_file}{DECRYPT_EXTENSION}'
            self.crypt.decrypt_file(self.local_file, output_file_path)

        logging.info("Descarga completada exitosamente.")
        self.jobq.put((self.idjob,
                 'completed',
                 None))

    def delete_file(self):
        fname = self.bucket_file
        bucket = self.bucket
        logging.info(f"Borrando fichero {fname} de bucket {bucket}")
        try:
            self.client.delete_object(Bucket=bucket, Key=fname)
            logging.info(f"Fichero {fname} borrado de bucket {bucket}")
        except ClientError as e:
            logging.error(f"Error al borrar el fichero {fname} del bucket {bucket}: {e}")
            raise
        self.jobq.put((self.idjob,
            'completed',
            None))

    def create_bucket(self):
        bucket = self.bucket
        logging.info(f"Creando bucket {bucket}")
        self.client.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint': self.region})
        logging.info(f"Bucket {bucket} creado")
        self.jobq.put((self.idjob,
            'completed',
            None))

    def delete_bucket(self):
        bucket = self.bucket
        bucket_resource = self.resource.Bucket(bucket)
        try:
            bucket_resource.objects.all().delete()
            logging.info(f"Objetos del bucket {bucket} borrados")
            bucket_resource.delete()
            logging.info(f"Bucket {bucket} borrado")
        except ClientError as e:
            logging.error(f"Error al borrar el bucket {bucket}: {e}")
            raise
        self.jobq.put((self.idjob,
            'completed',
            None))

    def run(self):
        self.client = boto3.client(S3_AWS_SERVICE, self.region)
        self.resource = boto3.resource(S3_AWS_SERVICE)
        self.ops[self.jobtype]()

        