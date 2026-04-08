from pdflatex import PDFLaTeX
from pathlib import Path
import os
from openai import OpenAI, OpenAIError

from consts import LATEX_TEMPLATE


class TexBuild:
    def __init__(self, group_name):
        self.template = LATEX_TEMPLATE
        self.group_name = group_name

    def create(self, content, name, idx):
        tex_filename = Path("temp.tex")

        renamed_content = content.replace("**name**", name)

        with tex_filename.open("a", encoding="utf-8") as tex_file:
            tex_file.write(self.template)
            tex_file.write(renamed_content)
            tex_file.write(r"\end{document}")

        pdf, _, _ = PDFLaTeX.from_texfile(str(tex_filename)).create_pdf()
        pdf_filename = (
            Path("exports") / group_name / f'{idx}_{name.replace(" ", "-")}.pdf'
        )
        pdf_filename.parent.mkdir(parents=True, exist_ok=True)

        pdf_filename.write_bytes(pdf)

        tex_filename.unlink()  # Remove temp.tex


class NoApiKey(Exception):
    pass


class Model:
    def __init__(self):
        self.api_key = self._load_api_key()
        self.client = self._load_client()

    def _load_api_key(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise NoApiKey(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
            )
        return api_key

    def _load_client(self):
        return OpenAI(api_key=self.api_key)
