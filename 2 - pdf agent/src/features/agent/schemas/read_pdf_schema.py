from pydantic import BaseModel

class ReadPDFInput(BaseModel):
    file_path: str