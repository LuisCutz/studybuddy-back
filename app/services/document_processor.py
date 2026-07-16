import os
import tempfile
import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from app.services.storage import StorageService
from app.services.text_extractor import extract_text_from_bytes

class DocumentProcessor:
    def __init__(self):
        self.storage_service = StorageService()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    async def process_pdf(self, file_key: str):
        print(f"[Processor] Descargando {file_key} desde R2...")
        
        pdf_bytes = await self.storage_service.get_file_content(file_key)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_file_path = temp_file.name

        try:
            print("[Processor] Extrayendo texto con LangChain...")
            loader = PyPDFLoader(temp_file_path)
            pages = loader.load()
            
            print("[Processor] Dividiendo texto en chunks...")
            chunks = self.text_splitter.split_documents(pages)
            
            print(f"[Processor] ¡Éxito! El PDF de {len(pages)} páginas se dividió en {len(chunks)} chunks.")
            
            if chunks:
                print(f"🔍 [Muestra Chunk 1]: {chunks[0].page_content[:200]}...")
            
            return chunks
            
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    async def process_file(
        self, 
        file_key: str, 
        filename: str, 
        document_id: uuid.UUID, 
        room_id: uuid.UUID
    ):
        # Descarga el archivo, extrae su texto sin importar el formato y lo parte en chunks para RAG.
        
        storage = StorageService()
        file_bytes = await storage.get_file_content(file_key)

        text = await extract_text_from_bytes(file_bytes, filename)

        if not text.strip():
             raise ValueError(f"No se pudo extraer texto del archivo {filename}.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        chunks_text = text_splitter.split_text(text)

        docs = [
            LangchainDocument(
                page_content=chunk,
                metadata={
                    "document_id": str(document_id), 
                    "room_id": str(room_id),
                    "source": filename
                }
            ) for chunk in chunks_text
        ]

        return docs