import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        # Busca un documento por su ID.
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def save(self, document: Document) -> Document:
        # Guarda un nuevo documento.
        self.db.add(document)
        await self.db.flush()
        return document

    async def delete(self, document: Document):
        # Elimina un documento de la base de datos.
        await self.db.delete(document)
        await self.db.flush()