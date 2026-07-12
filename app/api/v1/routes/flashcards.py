import uuid
import fitz
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.flashcard_deck import FlashcardDeck
from app.models.flashcard import Flashcard
from app.models.flashcard_deck_view import FlashcardDeckView
from app.services.llm.factory import get_llm_service
from app.services.storage import StorageService

from app.schemas.flashcard import (
    DeckCreateEmpty, DeckGenerateRequest, DeckUpdate, 
    DeckResponse, DeckWithCardsResponse, 
    FlashcardCreate, FlashcardResponse, FlashcardLLMEditRequest
)

router = APIRouter()


@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_empty_deck(
    payload: DeckCreateEmpty,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_deck = FlashcardDeck(
        subject_id=payload.subject_id,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description
    )
    db.add(new_deck)
    await db.commit()
    await db.refresh(new_deck)
    return new_deck

@router.post("/decks/generate", response_model=DeckWithCardsResponse, status_code=status.HTTP_201_CREATED)
async def generate_deck(
    payload: DeckGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc_result = await db.execute(select(Document).where(Document.id == payload.document_id))
    document = doc_result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")

    storage = StorageService()
    file_key = document.file_path.split("/", 1)[1] if "/" in document.file_path else document.file_path
    pdf_bytes = await storage.get_file_content(file_key)
    
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    llm_service = get_llm_service()
    generated_data = await llm_service.generate_flashcards(text=text, num_cards=payload.num_cards)

    new_deck = FlashcardDeck(
        subject_id=document.subject_id,
        user_id=current_user.id,
        title=generated_data.get("title", f"Flashcards de {document.title}"),
        description=payload.description or "Generado con IA"
    )
    db.add(new_deck)
    await db.flush()

    cards_to_insert = [
        Flashcard(deck_id=new_deck.id, front=card["front"], back=card["back"])
        for card in generated_data.get("cards", [])
    ]
    db.add_all(cards_to_insert)
    await db.commit()

    result = await db.execute(select(FlashcardDeck).options(selectinload(FlashcardDeck.flashcards)).where(FlashcardDeck.id == new_deck.id))
    return result.scalar_one()

@router.get("/decks", response_model=list[DeckResponse])
async def list_my_decks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(FlashcardDeck).where(FlashcardDeck.user_id == current_user.id))
    return list(result.scalars().all())

@router.get("/decks/{deck_id}", response_model=DeckWithCardsResponse)
async def get_deck(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(FlashcardDeck)
        .options(selectinload(FlashcardDeck.flashcards))
        .where(FlashcardDeck.id == deck_id)
    )
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Mazo no encontrado.")

    if deck.user_id != current_user.id:
        view = FlashcardDeckView(deck_id=deck.id, viewer_id=current_user.id)
        db.add(view)
        await db.commit()

    return deck

@router.put("/decks/{deck_id}", response_model=DeckResponse)
async def update_deck(
    deck_id: uuid.UUID,
    payload: DeckUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(FlashcardDeck).where(FlashcardDeck.id == deck_id, FlashcardDeck.user_id == current_user.id))
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Mazo no encontrado o sin permisos.")

    if payload.title is not None:
        deck.title = payload.title
    if payload.description is not None:
        deck.description = payload.description

    await db.commit()
    await db.refresh(deck)
    return deck

@router.delete("/decks/{deck_id}")
async def delete_deck(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(FlashcardDeck).where(FlashcardDeck.id == deck_id, FlashcardDeck.user_id == current_user.id))
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Mazo no encontrado o sin permisos.")

    await db.delete(deck)
    await db.commit()
    return {"message": "Mazo y sus tarjetas eliminados correctamente."}


@router.post("/decks/{deck_id}/cards", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
async def add_card_to_deck(
    deck_id: uuid.UUID,
    payload: FlashcardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    deck_result = await db.execute(select(FlashcardDeck).where(FlashcardDeck.id == deck_id, FlashcardDeck.user_id == current_user.id))
    if not deck_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar este mazo.")

    new_card = Flashcard(deck_id=deck_id, front=payload.front, back=payload.back)
    db.add(new_card)
    await db.commit()
    await db.refresh(new_card)
    return new_card

@router.put("/cards/{card_id}/llm-edit", response_model=FlashcardResponse)
async def edit_card_with_llm(
    card_id: uuid.UUID,
    payload: FlashcardLLMEditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Flashcard).join(FlashcardDeck).where(Flashcard.id == card_id, FlashcardDeck.user_id == current_user.id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada o sin permisos.")

    llm_service = get_llm_service()
    
    try:
        edited_data = await llm_service.edit_flashcard(
            front=card.front,
            back=card.back,
            instructions=payload.instructions
        )
        
        card.front = edited_data.get("front", card.front)
        card.back = edited_data.get("back", card.back)
        
        await db.commit()
        await db.refresh(card)
        return card
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de la IA al editar: {str(e)}")

@router.delete("/cards/{card_id}")
async def delete_card(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Flashcard).join(FlashcardDeck).where(Flashcard.id == card_id, FlashcardDeck.user_id == current_user.id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada o sin permisos.")

    await db.delete(card)
    await db.commit()
    return {"message": "Tarjeta eliminada correctamente."}