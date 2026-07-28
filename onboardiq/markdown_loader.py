import re
import yaml
from pathlib import Path
from typing import List
from langchain_core.documents import Document

class MarkdownFrontmatterLoader:
    """Loader to parse Markdown and Notion documents, extracting frontmatter metadata and RBAC roles."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)

    def load(self) -> List[Document]:
        if not self.file_path.exists():
            return []

        try:
            content = self.file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading Markdown file {self.file_path}: {e}")
            return []

        metadata = {
            "source": str(self.file_path),
            "type": "markdown",
            "access_roles": ["all"]  # default
        }

        # 1. Check for YAML Frontmatter (starts with ---)
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            body_content = content[frontmatter_match.end():]
            
            try:
                # Use a safe YAML parser
                data = yaml.safe_load(frontmatter_text)
                if isinstance(data, dict):
                    # Clean and copy keys
                    for k, v in data.items():
                        key_lower = k.lower().replace("-", "_")
                        
                        # Special handling for lists / roles
                        if key_lower == "access_roles":
                            if isinstance(v, list):
                                metadata["access_roles"] = [str(item).strip() for item in v]
                            elif isinstance(v, str):
                                metadata["access_roles"] = [item.strip() for item in v.split(",") if item.strip()]
                        elif key_lower == "tags" and isinstance(v, list):
                            metadata["tags"] = [str(item).strip() for item in v]
                        else:
                            metadata[key_lower] = v
            except Exception as e:
                print(f"Error parsing frontmatter in {self.file_path}: {e}")
        else:
            # No frontmatter block. Look for inline metadata line at top (e.g. Access-Roles: [engineering, ops])
            body_content = content
            # Try to match a line like "Access-Roles: [engineering, ops, admin]" in the first 5 lines
            lines = content.split("\n")[:5]
            for line in lines:
                match = re.match(r"^access[-_]roles:\s*\[?(.*?)\]?$", line, re.IGNORECASE)
                if match:
                    roles_str = match.group(1)
                    metadata["access_roles"] = [r.strip() for r in roles_str.split(",") if r.strip()]
                    break

        # If a title is parsed, keep it, otherwise set default from filename
        if "title" not in metadata:
            metadata["title"] = self.file_path.stem.replace("_", " ").title()

        return [Document(page_content=body_content, metadata=metadata)]
