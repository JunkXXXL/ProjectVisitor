from pathlib import Path


class SimpleChunker:
    def __init__(self):
        self.formats = [".txt"]

    def invoke(self, doc_path: Path) -> list[str]:
        if doc_path.suffix in self.formats:
            with doc_path.open('r', encoding='utf-8') as fl:
                content = fl.read()
            content = content.split('\n')
            content = [x for x in content if x != ""]
            return content
