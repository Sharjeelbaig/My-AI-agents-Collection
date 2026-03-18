from langchain_core.tools import StructuredTool
from .create_pdf import create_pdf
from .edit_pdf import edit_pdf
from .read_pdf import read_pdf
from ..schemas.create_pdf_input import CreatePDFInput
from ..schemas.edit_pdf_input import EditPDFInput
from ..schemas.read_pdf_schema import ReadPDFInput

create_pdf_tool = StructuredTool(
    name="create_pdf",
    func=create_pdf,
    description="Creates a PDF file with the given text. Input should be a dictionary with 'file_path' and 'text' keys.",
    args_schema=CreatePDFInput
)

read_pdf_tool = StructuredTool(
    name="read_pdf",
    func=read_pdf,
    description="Reads the text from a PDF file. Input should be a dictionary with a 'file_path' key.",
    args_schema=ReadPDFInput
)

edit_pdf_tool = StructuredTool(
    name="edit_pdf",
    func=edit_pdf,
    description="Edits a PDF file by adding new text. Input should be a dictionary with 'input_path', 'output_path', and 'new_text' keys.",
    args_schema=EditPDFInput
)

__all__ = ["create_pdf_tool", "read_pdf_tool", "edit_pdf_tool"]