from pydantic import BaseModel

class EditPDFInput(BaseModel):
    input_path: str
    output_path: str
    new_text: str