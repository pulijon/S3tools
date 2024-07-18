import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from s3ops import S3Ops
from s3crypt import S3Crypt
import os

DEFAULT_ENV_CRYPT_KEY = 'S3_CRYPT_KEY'
DEFAULT_REGION = 'us-east-2'
DEFAULT_STORAGE_CLASS ='STANDARD'
CRYPT_EXTENSION = ".s3enc"
DECRYPT_EXTENSION = ".s3dec"

class S3App:
    def __init__(self, root):
        self.root = root
        self.root.title("S3 Manager")

        self.ops = S3Ops(region=DEFAULT_REGION, 
                         storage_class=DEFAULT_STORAGE_CLASS)
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
        self.load_buckets()

    def create_bucket(self):
        bucket_name = simpledialog.askstring("Crear Bucket", "Introduce el nombre del nuevo bucket:")
        if bucket_name:
            try:
                self.ops.create_bucket(bucket_name)
                self.tree.insert('', 'end', bucket_name, text=bucket_name, values=[bucket_name])
                messagebox.showinfo("Éxito", f"Bucket {bucket_name} creado exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear el bucket {bucket_name}: {e}")
                
    def load_buckets(self):
        buckets = self.ops.list_buckets()
        for bucket in buckets:
            self.tree.insert('', 'end', bucket, text=bucket, values=[bucket])
            self.load_files(bucket)

    def on_open(self, event):
        item = self.tree.focus()
        if self.tree.parent(item) == '':
            self.load_files(item)

    def on_select(self, event):
        pass

    def load_files(self, bucket_name):
        files = self.ops.list_files(bucket_name)
        self.tree.delete(*self.tree.get_children(bucket_name))
        for file in files:
            self.tree.insert(bucket_name, 'end', f"{bucket_name}/{file}", text=file, values=[file])

    def upload_file(self):
        bucket_name = self.get_selected_bucket()
        if not bucket_name:
            messagebox.showwarning("Advertencia", "Selecciona un bucket primero")
            return
        file_path = filedialog.askopenfilename()
        if file_path:
            storage_class = self.storage_var.get()
            if self.encrypt_var.get():
                output_file_path = f'{file_path}{CRYPT_EXTENSION}'
                self.crypt.encrypt_file(file_path, output_file_path)
                file_path = output_file_path
            self.ops.upload_file_to_bucket(bucket_name, file_path, storage_class=storage_class)
            self.load_files(bucket_name)

    def download_file(self):
        item = self.tree.focus()
        if not item or '/' not in item:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return
        bucket_name, file_name = item.split('/', 1)
        dest_path = filedialog.asksaveasfilename(initialfile=file_name)
        if dest_path:
            self.ops.download_file_from_bucket(bucket_name, file_name, dest_path)
            if self.encrypt_var.get():
                dest_root, dest_ext = os.path.splitext(dest_path)
                output_file_path = dest_root if dest_ext == CRYPT_EXTENSION else f'{dest_path}{DECRYPT_EXTENSION}'
                self.crypt.decrypt_file(dest_path, output_file_path)

    def delete_file(self):
        item = self.tree.focus()
        if not item or '/' not in item:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return
        bucket_name, file_name = item.split('/', 1)
        confirm = messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas borrar el archivo {file_name}?")
        if confirm:
            self.ops.delete_file(bucket_name, file_name)
            self.load_files(bucket_name)

    def delete_bucket(self):
        bucket_name = self.get_selected_bucket()
        if not bucket_name:
            messagebox.showwarning("Advertencia", "Selecciona un bucket primero")
            return
        confirm = messagebox.askyesno("Confirmar", f"¿Estás seguro de que deseas borrar el bucket {bucket_name} y todos sus archivos?")
        if confirm:
            self.ops.delete_bucket(bucket_name)
            self.tree.delete(bucket_name)

    def get_selected_bucket(self):
        item = self.tree.focus()
        if self.tree.parent(item) == '':
            return item
        else:
            return self.tree.parent(item)

if __name__ == "__main__":
    root = tk.Tk()
    app = S3App(root)
    root.mainloop()