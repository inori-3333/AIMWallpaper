from pydantic import BaseModel


class ChatMessageIn(BaseModel):
    type: str  # "user_message" | "annotation"
    content: str = ""
    region: dict | None = None
    label: str = ""


class ChatMessageOut(BaseModel):
    type: str  # "ai_message" | "ai_thinking" | "generation_start" | "generation_progress" | "generation_complete" | "ai_question" | "error"
    content: str = ""
    task: str = ""
    progress: float = 0.0
    preview_url: str = ""
    question_id: str = ""
    code: str = ""
    message: str = ""
