from pydantic import BaseModel

class CreatePDFInput(BaseModel):
    file_path: str
    text: str