import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db, AsyncSessionLocal
from app.models.study_room_member import StudyRoomMember
from app.services.storage import StorageService
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.llm.factory import get_llm_service
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.repositories.document_repository import DocumentRepository

router = APIRouter()

# Pipeline de indexación en segundo plano
async def process_document_background(document_id: uuid.UUID, file_path: str):
    print(f"[Background] Iniciando indexación del documento {document_id}...")
    
    try:
        async with AsyncSessionLocal() as db:
            doc_repo = DocumentRepository(db)
            document = await doc_repo.get_by_id(document_id)
            
            if not document:
                print(f"[Background] Registro del documento {document_id} no encontrado.")
                return

            processor = DocumentProcessor()
            storage_service = StorageService()
            
            file_key = file_path.split(f"{storage_service.bucket_name}/")[-1]
            
            chunks = await processor.process_pdf(file_key)
            
            vector_service = VectorStoreService()
            await vector_service.add_documents(
                room_id=document.room_id,
                document_id=document.id,
                chunks=chunks
            )
            
            document.status = "completed"
            await db.commit()
            print(f"[Background] Documento {document_id} totalmente indexado y listo para RAG.")
            
    except Exception as e:
        print(f"[Background] Error crítico en el pipeline del documento {document_id}: {e}")
        async with AsyncSessionLocal() as db:
            doc_repo = DocumentRepository(db)
            document = await doc_repo.get_by_id(document_id)
            if document:
                document.status = "failed"
                await db.commit()

@router.get("/health", summary="Check Documents API Health")
async def documents_health_check():
    # Retorna el estado de salud y metadatos del módulo de Documentos.
    return {
        "status": "ok",
        "module": "Documents & RAG API",
        "version": "v1",
        "visibility": "private",
        "requires_jwt": True,
        "documentation": {
            "swagger_url": "/docs",
            "openapi_json_url": "/openapi.json"
        }
    }

# Subir documento
@router.post("/", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    room_id: uuid.UUID = Form(...), 
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    member_check = await db.execute(
        select(StudyRoomMember).where(StudyRoomMember.room_id == room_id, StudyRoomMember.user_id == current_user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="No tienes acceso a esta sala de estudio.")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")

    storage_service = StorageService()
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"rooms/{room_id}/{uuid.uuid4()}.{file_extension}"
    
    try:
        r2_path = await storage_service.upload_file(file, unique_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    new_document = Document(
        room_id=room_id,
        title=title,
        file_path=r2_path,
        status="pending"
    )

    doc_repo = DocumentRepository(db)
    await doc_repo.save(new_document)
    await db.commit()
    await db.refresh(new_document)

    background_tasks.add_task(process_document_background, new_document.id, r2_path)
    return new_document

# Descargar pdf
@router.get("/{document_id}/download")
async def get_document_download_url(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    ):
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    
    member_check = await db.execute(
        select(StudyRoomMember).where(StudyRoomMember.room_id == document.room_id, StudyRoomMember.user_id == current_user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="No tienes acceso a este documento.")
    
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
    ):
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    member_check = await db.execute(
        select(StudyRoomMember).where(StudyRoomMember.room_id == document.room_id, StudyRoomMember.user_id == current_user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar en esta sala.")
        
    storage_service = StorageService()
    file_key = document.file_path.split(f"{storage_service.bucket_name}/")[-1]
    
    try:
        await storage_service.delete_file(file_key)
        
        vector_service = VectorStoreService()
        await vector_service.delete_document_embeddings(
            room_id=document.room_id,
            document_id=document.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    await doc_repo.delete(document)
    await db.commit()
    
    return {"message": "Documento y vectores purgados con éxito de todo el sistema."}

# Generar resumen desde el índice
@router.get("/{document_id}/summary")
async def get_document_summary(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    member_check = await db.execute(
        select(StudyRoomMember).where(StudyRoomMember.room_id == document.room_id, StudyRoomMember.user_id == current_user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="No tienes acceso a este documento.")
        
    if document.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail="El documento aún se está procesando o falló la indexación."
        )

    try:
        vector_service = VectorStoreService()
        index_text = await vector_service.get_document_index_chunks(
            room_id=document.room_id,
            document_id=document.id
        )
        
        if not index_text:
            return {"summary": "La Inteligencia Artificial no pudo localizar un índice claro en este documento."}

        llm = get_llm_service()
        
        prompt_personalizado = f"""
        A continuación te proporciono fragmentos extraídos del índice o temario de un documento.
        Utilizando ÚNICAMENTE los temas mencionados aquí, redacta un resumen general y fluido de lo que trata el material.
        Estructúralo en párrafos cortos y viñetas claras. No inventes información que no esté en el texto.

        ÍNDICE EXTRAÍDO:
        {index_text}
        """
        
        print("[LLM] Generando resumen a partir del índice...")
        summary = await llm.generate_response(prompt_personalizado)
        
        return {
            "document_id": document.id,
            "title": document.title,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))