from util import logcfg
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from s3job import S3job
from s3crypt import S3Crypt
import threading
import queue
import uuid

DEFAULT_ENV_CRYPT_KEY = 'S3_CRYPT_KEY'
DEFAULT_REGION = 'us-east-2'
DEFAULT_STORAGE_CLASS ='STANDARD'
CRYPT_EXTENSION = ".s3enc"
DECRYPT_EXTENSION = ".s3dec"

class S3App:
    def __init__(self, root):
        self.root = root
        self.root.title("S3 Manager")

        self.crypt = S3Crypt(DEFAULT_ENV_CRYPT_KEY)

        self.storage_classes = [
            'STANDARD',
            'INTELLIGENT_TIERING',
            'STANDARD_IA',
            'ONEZONE_IA',
            'GLACIER',
            'GLACIER_IR',
            'DEEP_ARCHIVE',
            'REDUCED_REDUNDANCY'
        ]

        self.tree = ttk.Treeview(root)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewOpen>>", self.on_open)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(fill=tk.X)

        self.storage_var = tk.StringVar(value=self.storage_classes[0])

        self.storage_menu = ttk.Combobox(self.btn_frame, textvariable=self.storage_var, values=self.storage_classes)
        self.storage_menu.pack(side=tk.LEFT, padx=5, pady=5)

        self.create_bucket_btn = tk.Button(self.btn_frame, text="Crear Bucket", command=self.create_bucket)
        self.create_bucket_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.upload_btn = tk.Button(self.btn_frame, text="Subir Archivo", command=self.upload_file)
        self.upload_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.download_btn = tk.Button(self.btn_frame, text="Descargar Archivo", command=self.download_file)
        self.download_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_file_btn = tk.Button(self.btn_frame, text="Borrar Archivo", command=self.delete_file)
        self.delete_file_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_bucket_btn = tk.Button(self.btn_frame, text="Borrar Bucket", command=self.delete_bucket)
        self.delete_bucket_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.encrypt_var = tk.IntVar()
        self.encrypt_check = tk.Checkbutton(self.btn_frame, text="Encriptar/Desencriptar", variable=self.encrypt_var)
        self.encrypt_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.jobs = {}
        self.qprog = queue.Queue()
        threading.Thread(target=self.manage_jobs, daemon=True).start()
        self.start_s3job('list_buckets')

    def start_s3job(self, op, **args):
        jobid = str(uuid.uuid4())
        newjob = S3job(jobid, op, self.qprog, **args)
        self.jobs[jobid] = newjob
        newjob.start()
         
    def manage_jobs(self):
        while True:
            idjob, event, data = self.qprog.get()
            logging.debug(f"Llega mensaje idjob={idjob}, event={event}, data={data}")
            if not idjob in self.jobs:
                logging.error(f"No hay job con id {idjob}")
                continue
            job = self.jobs[idjob]
            if event == 'completed':
                logging.info(f"Tarea {idjob} terminada")
                jobtype = job.jobtype
                
                # Dependiendo de la tarea que se acaba, hay que hacer cosas distintas
                if jobtype == 'list_buckets':
                    buckets = data
                    self.tree.delete(*self.tree.get_children(''))
                    for bucket in buckets:
                        self.tree.insert('', 'end', bucket, text=bucket, values=[bucket])
                        self.start_s3job('list_files', bucket=bucket)
                elif jobtype == 'list_files':
                    files = data
                    bucket = job.bucket
                    self.tree.delete(*self.tree.get_children(bucket))
                    for file in files:
                        self.tree.insert(bucket, 'end', f"{bucket}/{file}", text=file, values=[file])
                elif jobtype == 'create_bucket':
                    self.start_s3job('list_buckets')
                elif jobtype == 'delete_bucket':
                    self.tree.delete(job.bucket)
                elif (jobtype == 'delete_file') or (jobtype == 'upload'):
                    self.start_s3job('list_files', bucket=job.bucket)
                    
                del self.jobs[idjob]

    def create_bucket(self):
        bucket = simpledialog.askstring("Crear Bucket", "Introduce el nombre del nuevo bucket:")
        if bucket:
            try:
                self.start_s3job('create_bucket', bucket=bucket)
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear el bucket {bucket}: {e}")
                
    def on_open(self, event):
        bucket = self.tree.focus()
        if self.tree.parent(bucket) == '':
           self.start_s3job('list_files', bucket=bucket)

    def on_select(self, event):
        pass

    def upload_file(self):
        bucket = self.get_selected_bucket()
        if not bucket:
            messagebox.showwarning("Advertencia", "Selecciona un bucket primero")
            return
        local_file = filedialog.askopenfilename()
        if local_file:
            storage_class = self.storage_var.get()
            self.start_s3job ('upload', 
                        bucket=bucket,
                        local_file=local_file,
                        crypt = self.crypt,
                        storage_class = storage_class,
                        encrypted = self.encrypt_var.get(),
                        root=self.root)


    def download_file(self):
        item = self.tree.focus()
        if not item or '/' not in item:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return
        bucket_name, file_name = item.split('/', 1)
        dest_path = filedialog.asksaveasfilename(initialfile=file_name)
        if dest_path:
            self.start_s3job('download', 
                        bucket=bucket_name,
                        bucket_file=file_name,
                        local_file=dest_path,
                        crypt = self.crypt,
                        encrypted = self.encrypt_var.get(),
                        root=self.root)

    def delete_file(self):
        item = self.tree.focus()
        if not item or '/' not in item:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return
        bucket, bucket_file = item.split('/', 1)
        confirm = messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas borrar el archivo {bucket_file}?")
        if confirm:
            self.start_s3job('delete_file', bucket=bucket, bucket_file=bucket_file)

    def delete_bucket(self):
        bucket_name = self.get_selected_bucket()
        if not bucket_name:
            messagebox.showwarning("Advertencia", "Selecciona un bucket primero")
            return
        confirm = messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas borrar el bucket {bucket_name} y todos sus archivos?")
        if confirm:
            self.start_s3job('delete_bucket', bucket=bucket_name)

    def get_selected_bucket(self):
        item = self.tree.focus()
        if self.tree.parent(item) == '':
            return item
        else:
            return self.tree.parent(item)

if __name__ == "__main__":
    logcfg(__name__)
    root = tk.Tk()
    app = S3App(root)
    root.mainloop()