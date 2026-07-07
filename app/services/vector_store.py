import os
import uuid
from langchain_chroma import Chroma
from app.services.llm.factory import get_llm_service

class VectorStoreService:
    def __init__(self):
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.llm_service = get_llm_service()
        self.embeddings = self.llm_service.get_embeddings()

    def get_vector_store(self, subject_id: uuid.UUID) -> Chroma:
        # Obtiene o crea una colección de Chroma aislada por materia.
        collection_name = f"subject_{str(subject_id).replace('-', '_')}"
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    async def add_documents(self, subject_id: uuid.UUID, document_id: uuid.UUID, chunks):
        # Indexa los chunks de LangChain en ChromaDB agregando metadata de control.
        # Sellar cada pedacito con metadatos para búsquedas y borrados quirúrgicos.
        for chunk in chunks:
            chunk.metadata["document_id"] = str(document_id)
            chunk.metadata["subject_id"] = str(subject_id)

        vector_store = self.get_vector_store(subject_id)
        
        vector_store.add_documents(chunks)
        print(f"[VectorStore] {len(chunks)} chunks guardados exitosamente en ChromaDB para la materia {subject_id}")

    async def delete_document_embeddings(self, subject_id: uuid.UUID, document_id: uuid.UUID):
        # Elimina de forma permanente todos los vectores pertenecientes a un documento.
        vector_store = self.get_vector_store(subject_id)
        vector_store.delete(where={"document_id": str(document_id)})
        print(f"[VectorStore] Vectores del documento {document_id} purgados de ChromaDB.")