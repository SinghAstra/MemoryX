from pydantic import BaseModel


class Document(BaseModel):
    id: str
    container_tag: str
    content: str
    content_hash: str
    custom_id: str | None = None
    status: str = "queued"
    created_at: str
    updated_at: str
