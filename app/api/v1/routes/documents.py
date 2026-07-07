import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.services.storage import StorageService
from app.models.document import Document
from app.schemas.document import DocumentResponse

router = APIRouter()

# Tarea en segundo plano
async def process_document_background(document_id: uuid.UUID, file_path: str):
    print(f"[Background] Iniciando indexación del documento {document_id}...")
    print(f"[Background] Leyendo archivo desde: {file_path}")

    import asyncio
    await asyncio.sleep(2)
    print(f"[Background] Documento {document_id} listo para usar con IA.")

# Subir documento
@router.post("/", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    subject_id: uuid.UUID = Form(...), 
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")

    storage_service = StorageService()

    file_extension = file.filename.split('.')[-1]
    unique_filename = f"subjects/{subject_id}/{uuid.uuid4()}.{file_extension}"
    
    try:
        r2_path = await storage_service.upload_file(file, unique_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_document = Document(
        subject_id=subject_id,
        title=title,
        file_path=r2_path,
        status="pending"
    )
    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)

    background_tasks.add_task(process_document_background, new_document.id, r2_path)

    return new_document

# Descargar pdf (Url temporal)
@router.get("/{document_id}/download")
async def get_document_download_url(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
        
    storage_service = StorageService()
    
    file_key = document.file_path.split(f"{storage_service.bucket_name}/")[-1]
    
    try:
        url = await storage_service.get_presigned_url(file_key, expiration_seconds=3600)
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Eliminar documento
@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
        
    storage_service = StorageService()
    file_key = document.file_path.split(f"{storage_service.bucket_name}/")[-1]
    
    try:
        await storage_service.delete_file(file_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    await db.delete(document)
    await db.commit()
    
    # TODO: Llamar a ChromaDB para borrar los vectores de este ID
    
    return {"message": "Documento eliminado exitosamente de la base de datos y la nube"}