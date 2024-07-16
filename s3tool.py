from util import logcfg
import logging
import datetime
import argparse
from getpass import getpass
from s3crypt import S3Crypt
from s3ops import S3Ops

# Configuración
S3_OPERATIONS = ['create',
                 'upload', 
                 'download', 
                 'list_buckets', 
                 'list_files',
                 'delete_file',
                 'delete_bucket',
                 'encrypt', 
                 'decrypt' ]

STORAGE_CLASSES= ['STANDARD',
                  'INTELLIGENT_TIERING',
                  'STANDARD_IA',
                  'ONEZONE_IA',
                  'GLACIER',
                  'GLACIER_IR',
                  'DEEP_ARCHIVE',
                  'REDUCED_REDUNDANCY'] 

def create(args):
    ops = S3Ops(region=args.region, 
                storage_class=args.storage_class)
    ops.create_bucket(args.bucket)  

def upload(args):
    ops = S3Ops(region=args.region, 
                storage_class=args.storage_class)
    ops.upload_file_to_bucket(args.bucket,
                              args.fname)   
def download(args):
    ops = S3Ops(region=args.region, 
                storage_class=args.storage_class)
    ops.download_file_from_bucket(args.bucket,
                                  args.fname,
                                  args.output_fname)

def list_buckets(args):
    ops = S3Ops(region=args.region, 
                storage_class=args.storage_class)
    logging.info(f"Los buckets disponibles son: {ops.list_buckets()}")

def list_files(args):
    ops = S3Ops(region=args.region, 
                storage_class=args.storage_class)
    logging.info(f"Los ficheros disponibles en {args.bucket} son: {ops.list_files(args.bucket)}")

def delete_file(args):
    ops = S3Ops(region=args.region, 
                storage_class=args.storage_class)
    ops.delete_file(args.bucket,
                    args.fname)

def delete_bucket(args):
    ops = S3Ops(region=args.region, 
                storage_class=args.storage_class)
    ops.delete_bucket(args.bucket)                                  

def encrypt(args):
    crypt = S3Crypt(args.env_crypt_key)
    crypt.encrypt_file(args.fname, args.output_fname)

def decrypt(args):
    crypt = S3Crypt(args.env_crypt_key)
    crypt.decrypt_file(args.fname, args.output_fname)


DEFAULT_VAULT = "default-vault"
DEFAULT_OPERATION = 'list_buckets'
DEFAULT_ENV_CRYPT_KEY = 'S3_CRYPT_KEY'
DEFAULT_REGION = 'us-east-2'

def main():
    args = get_pars()
    logging.info(f"{args}")
    globals()[args.operation](args)


def get_pars():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=S3_OPERATIONS, type=str, default=DEFAULT_OPERATION,
                        help=f"operación a realizar. Por defecto, {DEFAULT_OPERATION}")
    parser.add_argument("-f", "--fname", type=str, 
                        help=f"archivo a procesar")
    parser.add_argument("-b", "--bucket", type=str, default=DEFAULT_VAULT,
                        help=f"modelo a utilizar. Por defecto, {DEFAULT_VAULT}")
    parser.add_argument("-k", "--env-crypt-key", type=str, default=DEFAULT_ENV_CRYPT_KEY,
                        help=f"variable de entorno con la clave de encriptación. Por defecto, {DEFAULT_ENV_CRYPT_KEY}")
    parser.add_argument("-o", "--output-fname", type=str,
                        help=f"fichero resultado")
    parser.add_argument("-r", "--region", type=str, default=DEFAULT_REGION,
                        help=f"fichero resultado")
    parser.add_argument("-s", "--storage-class", choices=STORAGE_CLASSES, type=str,
                        help=f"fichero resultado")

    return parser.parse_args()

if __name__ == "__main__":
    logcfg(__file__)

    stime = datetime.datetime.now()
    main()
    etime = datetime.datetime.now()
    logging.info(f"Ejecución del programa ha tardado {etime - stime}")
    exit(0)
