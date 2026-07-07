import os
import aioboto3
from fastapi import UploadFile
from botocore.exceptions import ClientError

class StorageService:
    def __init__(self):
        self.account_id = os.getenv("R2_ACCOUNT_ID")
        self.access_key = os.getenv("R2_ACCESS_KEY_ID")
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("R2_BUCKET_NAME", "studybuddy-docs")
        
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        
        self.session = aioboto3.Session()

    async def upload_file(self, file: UploadFile, file_name: str) -> str:
        # Sube un archivo a Cloudflare R2 y retorna la ruta del archivo.
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto"
        ) as client:
            try:
                file_content = await file.read()
                
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_name,
                    Body=file_content,
                    ContentType=file.content_type
                )
                
                return f"{self.bucket_name}/{file_name}"
                
            except ClientError as e:
                print(f"Error subiendo archivo a R2: {e}")
                raise Exception("No se pudo subir el documento al servidor de almacenamiento.")

    async def get_presigned_url(self, file_name: str, expiration_seconds: int = 3600) -> str:
        # Genera una URL temporal para que el frontend pueda descargar el PDF directo desde R2.
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto"
        ) as client:
            try:
                url = await client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket_name, "Key": file_name},
                    ExpiresIn=expiration_seconds
                )
                return url
            except ClientError as e:
                print(f"Error generando URL pre-firmada: {e}")
                raise Exception("No se pudo generar el link de descarga.")
            
    async def delete_file(self, file_key: str) -> bool:
        # Elimina un archivo físico de Cloudflare R2.
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto"
        ) as client:
            try:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                return True
            except ClientError as e:
                print(f"Error eliminando archivo de R2: {e}")
                raise Exception("No se pudo eliminar el documento del servidor de almacenamiento.")