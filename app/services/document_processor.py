import os
import tempfile
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.storage import StorageService

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