import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession
from app.models.chat_message import ChatMessage
from app.models.document import Document
from app.repositories.chat_repository import ChatRepository
from app.services.llm.factory import get_llm_service
from app.services.vector_store import VectorStoreService


class ChatService:
    def __init__(self, db: AsyncSession | None):
        self.db = db
        self.repo = ChatRepository(db) if db is not None else None

    def _build_prompt(
        self,
        user_message: str,
        context_text: str,
        history: list[dict[str, str]],
        citations: list[dict[str, Any]],
    ) -> str:
        history_text = "\n".join(
            [f"{item.get('role', 'user').upper()}: {item.get('content', '')}" for item in history]
        ) or "Sin historial previo."
        citations_text = "\n".join(
            [f"- {citation.get('title', 'Documento')} ({citation.get('document_id', '')})" for citation in citations]
        ) or "No se proporcionaron citas."

        return f"""Actúa como un asistente académico y responde usando únicamente el contexto proporcionado.

Contexto relevante:
{context_text or 'No se encontró contexto relevante.'}

Historial de conversación:
{history_text}

Citas disponibles:
{citations_text}

Mensaje actual del usuario:
{user_message}
"""

    async def create_session(
        self,
        user_id: uuid.UUID,
        room_id: uuid.UUID,
        name: str | None,
        document_ids: list[uuid.UUID],
    ) -> ChatSession:
        if self.db is None:
            raise RuntimeError("Se requiere una sesión de base de datos para crear una sesión de chat.")

        documents: list[Document] = []
        if document_ids:
            result = await self.db.execute(select(Document).where(Document.id.in_(document_ids)))
            documents = list(result.scalars().all())
            if len(documents) != len(set(document_ids)):
                raise ValueError("Uno o más documentos no existen.")
            for document in documents:
                if document.room_id != room_id:
                    raise ValueError("Los documentos deben pertenecer a la misma sala de la sesión.")

        session = ChatSession(
            user_id=user_id,
            room_id=room_id,
            name=name or "Nueva sesión",
            documents=documents
        )
        self.db.add(session)
        
        await self.db.flush()
        session_id = session.id 
        
        await self.db.commit()
        
        return await self.get_session(session_id, user_id)

    async def list_sessions(self, user_id: uuid.UUID) -> list[ChatSession]:
        if self.db is None:
            raise RuntimeError("Se requiere una sesión de base de datos para listar sesiones.")

        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.documents))
            .order_by(ChatSession.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession:
        if self.db is None:
            raise RuntimeError("Se requiere una sesión de base de datos para obtener una sesión de chat.")

        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.documents), selectinload(ChatSession.messages))
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError("Sesión no encontrada.")
        return session

    async def update_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str | None,
        document_ids: list[uuid.UUID] | None,
    ) -> ChatSession:
        session = await self.get_session(session_id, user_id)

        if name is not None:
            session.name = name

        if document_ids is not None:
            if document_ids:
                result = await self.db.execute(select(Document).where(Document.id.in_(document_ids)))
                documents = list(result.scalars().all())
                if len(documents) != len(set(document_ids)):
                    raise ValueError("Uno o más documentos no existen.")
                for document in documents:
                    if document.room_id != session.room_id:
                        raise ValueError("Los documentos deben pertenecer a la misma sala de la sesión.")
            else:
                documents = []
            session.documents = documents

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        session = await self.get_session(session_id, user_id)
        await self.db.delete(session)
        await self.db.commit()
        return True

    async def list_messages(self, session_id: uuid.UUID, user_id: uuid.UUID) -> list[ChatMessage]:
        await self.get_session(session_id, user_id)
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def send_message(self, session_id: uuid.UUID, user_id: uuid.UUID, content: str) -> dict[str, Any]:
        if self.db is None:
            raise RuntimeError("Se requiere una sesión de base de datos para enviar mensajes.")

        session = await self.get_session(session_id, user_id)
        user_message = ChatMessage(session_id=session.id, role="user", content=content)
        self.db.add(user_message)
        await self.db.flush()

        history = [
            {"role": message.role, "content": message.content}
            for message in await self.list_messages(session_id, user_id)
            if message.id != user_message.id
        ]

        vector_service = VectorStoreService()
        context_text, citations = await self._build_context(session, content, vector_service)
        prompt = self._build_prompt(
            user_message=content,
            context_text=context_text,
            history=history,
            citations=citations,
        )

        llm_service = get_llm_service()
        response_content = await llm_service.generate_response(prompt)

        if isinstance(response_content, list):
            response_content = "".join(
                [bloque.get("text", "") for bloque in response_content if isinstance(bloque, dict)]
            )
        elif not isinstance(response_content, str):
            response_content = str(response_content)

        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_content,
            citations=citations,
        )
        self.db.add(assistant_message)
        await self.db.commit()
        await self.db.refresh(user_message)
        await self.db.refresh(assistant_message)

        return {
            "user_message": user_message,
            "assistant_message": assistant_message,
        }

    async def delete_message(self, session_id: uuid.UUID, user_id: uuid.UUID, message_id: uuid.UUID) -> bool:
        await self.get_session(session_id, user_id)
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id, ChatMessage.session_id == session_id)
        )
        message = result.scalar_one_or_none()
        if message is None:
            raise ValueError("Mensaje no encontrado.")
        await self.db.delete(message)
        await self.db.commit()
        return True

    async def regenerate_last_response(self, session_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        if self.db is None:
            raise RuntimeError("Se requiere una sesión de base de datos para regenerar una respuesta.")

        session = await self.get_session(session_id, user_id)
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = list(result.scalars().all())
        if not messages:
            raise ValueError("No hay mensajes en la sesión para regenerar.")

        assistant_message = next((message for message in reversed(messages) if message.role == "assistant"), None)
        if assistant_message is None:
            raise ValueError("No hay respuestas previas para regenerar.")

        prompt_message = None
        for message in reversed(messages):
            if message.id == assistant_message.id:
                break
            if message.role == "user":
                prompt_message = message
                break

        if prompt_message is None:
            raise ValueError("No se encontró el prompt original para regenerar la respuesta.")

        history = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.id != prompt_message.id and message.id != assistant_message.id
        ]

        vector_service = VectorStoreService()
        context_text, citations = await self._build_context(session, prompt_message.content, vector_service)
        prompt = self._build_prompt(
            user_message=prompt_message.content,
            context_text=context_text,
            history=history,
            citations=citations,
        )

        llm_service = get_llm_service()
        response_content = await llm_service.generate_response(prompt)

        if isinstance(response_content, list):
            response_content = "".join(
                [bloque.get("text", "") for bloque in response_content if isinstance(bloque, dict)]
            )
        elif not isinstance(response_content, str):
            response_content = str(response_content)

        regenerated_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_content,
            citations=citations,
        )
        self.db.add(regenerated_message)
        await self.db.commit()
        await self.db.refresh(regenerated_message)

        return {
            "user_message": prompt_message,
            "assistant_message": regenerated_message,
        }

    async def _build_context(
        self,
        session: ChatSession,
        query: str,
        vector_service: VectorStoreService,
    ) -> tuple[str, list[dict[str, Any]]]:
        if not session.documents:
            return "", []

        context_chunks: list[str] = []
        citations: list[dict[str, Any]] = []
        for document in session.documents:
            vector_store = vector_service.get_vector_store(session.room_id)
            results = vector_store.similarity_search(
                query=query,
                k=3,
                filter={"document_id": str(document.id)},
            )
            if not results:
                continue

            document_context = "\n\n".join(result.page_content for result in results)
            context_chunks.append(f"[Documento: {document.title}]\n{document_context}")
            citations.extend(
                [
                    {
                        "document_id": str(document.id),
                        "title": document.title,
                        "snippet": result.page_content[:250],
                    }
                    for result in results
                ]
            )

        return "\n\n".join(context_chunks), citations
