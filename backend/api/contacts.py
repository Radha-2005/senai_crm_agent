"""
api/contacts.py - Contact management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.session import get_db
from backend.db.models import Contact
from backend.schemas.email import ContactCreate, ContactResponse

router = APIRouter(prefix="/api/v1", tags=["contacts"])


@router.get(
    "/contacts",
    response_model=List[ContactResponse],
    summary="List all contacts",
)
async def list_contacts(
    tier: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[ContactResponse]:
    """List all contacts with optional tier filter and pagination."""
    query = select(Contact).order_by(Contact.created_at.desc())
    
    if tier:
        query = query.where(Contact.tier == tier)
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    contacts = result.scalars().all()
    return [ContactResponse.model_validate(c) for c in contacts]


@router.get(
    "/contacts/{contact_id}",
    response_model=ContactResponse,
    summary="Get contact by ID",
)
async def get_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    """Get a single contact by ID."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact {contact_id} not found",
        )
    
    return ContactResponse.model_validate(contact)


@router.put(
    "/contacts/{contact_id}",
    response_model=ContactResponse,
    summary="Update contact",
)
async def update_contact(
    contact_id: str,
    body: ContactCreate,
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    """Update an existing contact's profile data."""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact {contact_id} not found",
        )
    
    for field, value in body.model_dump(exclude_unset=True).items():
        if hasattr(contact, field) and field != "id":
            setattr(contact, field, value)
    
    await db.commit()
    return ContactResponse.model_validate(contact)
