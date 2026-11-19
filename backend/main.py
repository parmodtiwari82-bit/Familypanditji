from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="AI Family Pandit Ji API", version="0.1.0")

# Production deployment must replace "*" with the actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="hi", pattern="^(hi|sa|en)$")

class AskResponse(BaseModel):
    answer: str
    mode: str = "beta-placeholder"
    needs_acharya_review: bool = True

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-family-pandit-ji", "version": "0.1.0"}

@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    # Safe placeholder: connect a vetted LLM + curated sources in the next phase.
    return AskResponse(
        answer=(
            "आपका प्रश्न प्राप्त हुआ। AI ज्ञान-सेवा अभी कॉन्फ़िगर नहीं है। "
            "कृपया किसी विशिष्ट पूजा-विधि या धार्मिक निर्णय की पुष्टि योग्य आचार्य से करें।"
        ),
        mode="beta-placeholder",
    )
