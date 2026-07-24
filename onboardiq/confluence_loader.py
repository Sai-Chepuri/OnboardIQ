from pathlib import Path
from typing import List
from bs4 import BeautifulSoup
from langchain_core.documents import Document

class ConfluenceHTMLLoader:
    """Loader to parse Confluence HTML exports, converting tables and panels to structured Markdown representations."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)

    def _parse_table(self, table_tag) -> str:
        """Converts an HTML table tag into a clean Markdown table string."""
        markdown_table = []
        rows = table_tag.find_all("tr")
        if not rows:
            return ""

        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True).replace("\n", " ") for cell in cells]
            
            # Form the table row
            markdown_table.append("| " + " | ".join(cell_texts) + " |")
            
            # Insert markdown header separator after the first header row
            if i == 0 and row.find("th"):
                separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                markdown_table.append(separator)

        return "\n" + "\n".join(markdown_table) + "\n"

    def _parse_element(self, element) -> str:
        """Helper to convert individual HTML elements into Markdown format."""
        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(element.name[1])
            return f"\n{'#' * level} {element.get_text(strip=True)}\n"
            
        elif element.name == "p":
            return f"\n{element.get_text(strip=True)}\n"
            
        elif element.name == "pre" or element.name == "code":
            return f"\n```\n{element.get_text()}\n```\n"
            
        elif element.name == "table":
            return self._parse_table(element)
            
        elif element.name in ["ul", "ol"]:
            list_items = []
            for j, li in enumerate(element.find_all("li", recursive=False)):
                prefix = f"{j + 1}." if element.name == "ol" else "*"
                list_items.append(f"{prefix} {li.get_text(strip=True)}")
            return "\n" + "\n".join(list_items) + "\n"
            
        elif element.name == "div" and "confluence-information-macro" in element.get("class", []):
            title_tag = element.find(class_="title")
            title = title_tag.get_text(strip=True) if title_tag else "NOTE"
            body_tag = element.find(class_="confluence-information-macro-body")
            body = body_tag.get_text(strip=True) if body_tag else element.get_text(strip=True)
            return f"\n> **{title}**\n> {body}\n"

        # Recursive text extraction for general containers
        text = element.get_text(strip=True)
        return f"\n{text}\n" if text else ""

    def load(self) -> List[Document]:
        """Loads and parses the Confluence HTML file."""
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
        except Exception as e:
            print(f"Error reading Confluence file {self.file_path}: {e}")
            return []

        # Extract metadata from meta tags
        meta_space = soup.find("meta", attrs={"name": "confluence-space"})
        meta_page_id = soup.find("meta", attrs={"name": "confluence-page-id"})
        meta_author = soup.find("meta", attrs={"name": "confluence-author"})
        meta_modified = soup.find("meta", attrs={"name": "confluence-last-modified"})

        space = meta_space.get("content", "Unknown") if meta_space else "Unknown"
        page_id = meta_page_id.get("content", "Unknown") if meta_page_id else "Unknown"
        author = meta_author.get("content", "Unknown") if meta_author else "Unknown"
        last_modified = meta_modified.get("content", "Unknown") if meta_modified else "Unknown"

        # Title extraction
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled Page"
        
        # If title tag is not set or empty, look for the first h1
        if not title or title == "Untitled Page":
            h1_tag = soup.find("h1")
            if h1_tag:
                title = h1_tag.get_text(strip=True)

        # Parse body blocks
        body = soup.find("body")
        markdown_blocks = []
        
        if body:
            # We iterate direct children of body to retain vertical sequence
            for child in body.find_all(recursive=False):
                markdown_blocks.append(self._parse_element(child))
        else:
            # Fallback if no body tag exists
            for child in soup.find_all(recursive=False):
                markdown_blocks.append(self._parse_element(child))

        formatted_content = f"# Confluence Page: {title}\n"
        formatted_content += f"Space: {space} | Author: {author} | Last Modified: {last_modified}\n"
        formatted_content += "\n".join([block for block in markdown_blocks if block.strip()])

        # Build document
        metadata = {
            "source": str(self.file_path),
            "type": "confluence",
            "title": title,
            "space": space,
            "page_id": page_id,
            "author": author,
            "last_modified": last_modified
        }
        
        return [Document(page_content=formatted_content, metadata=metadata)]
