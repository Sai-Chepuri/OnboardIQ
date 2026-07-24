import sys
from pathlib import Path
from onboardiq.config import DATA_DIR
from onboardiq.slack_loader import SlackDirectoryLoader
from onboardiq.confluence_loader import ConfluenceHTMLLoader
from onboardiq.chunker import WorkspaceChunker
from langchain_community.document_loaders import TextLoader

def load_all_documents():
    """Loads all dummy Markdown, Notion, Confluence, and Slack files."""
    docs = []
    
    # 1. Load standard markdown
    markdown_path = DATA_DIR / "markdown" / "payment_gateway.md"
    if markdown_path.exists():
        loader = TextLoader(str(markdown_path))
        md_docs = loader.load()
        for doc in md_docs:
            doc.metadata["type"] = "markdown"
            doc.metadata["source"] = "data/markdown/payment_gateway.md"
        docs.extend(md_docs)

    # 2. Load Notion markdown
    for notion_path in (DATA_DIR / "notion").glob("*.md"):
        loader = TextLoader(str(notion_path))
        notion_docs = loader.load()
        for doc in notion_docs:
            doc.metadata["type"] = "markdown"
            doc.metadata["source"] = f"data/notion/{notion_path.name}"
        docs.extend(notion_docs)

    # 3. Load Confluence HTML
    confluence_path = DATA_DIR / "confluence" / "release_runbook.html"
    if confluence_path.exists():
        loader = ConfluenceHTMLLoader(confluence_path)
        docs.extend(loader.load())

    # 4. Load Slack JSON
    slack_loader = SlackDirectoryLoader(DATA_DIR / "slack")
    docs.extend(slack_loader.load())

    return docs

def test_chunker():
    print("Loading documents...")
    docs = load_all_documents()
    print(f"Loaded {len(docs)} document objects.")

    print("\nInitializing Workspace Chunker...")
    chunker = WorkspaceChunker(chunk_size=400, chunk_overlap=50) # smaller chunk sizes to force splits
    chunks = chunker.split_documents(docs)
    print(f"Generated {len(chunks)} chunks.")

    print("\n=== Reviewing Chunk Samples ===")
    
    # Sample from standard markdown/confluence
    md_confl_chunks = [c for c in chunks if c.metadata.get("type") in ["markdown", "confluence"]]
    print(f"\n--- Markdown/Confluence Chunk Sample (Count: {len(md_confl_chunks)}) ---")
    if md_confl_chunks:
        sample = md_confl_chunks[0]
        print(f"Metadata: {sample.metadata}")
        print("Page Content:")
        print(sample.page_content)
        print("-" * 50)
        if len(md_confl_chunks) > 1:
            sample2 = md_confl_chunks[1]
            print(f"Metadata: {sample2.metadata}")
            print("Page Content:")
            print(sample2.page_content)
            print("-" * 50)

    # Sample from Slack
    slack_chunks = [c for c in chunks if c.metadata.get("type") == "slack"]
    print(f"\n--- Slack Chunk Sample (Count: {len(slack_chunks)}) ---")
    if slack_chunks:
        sample = slack_chunks[0]
        print(f"Metadata: {sample.metadata}")
        print("Page Content:")
        print(sample.page_content)
        print("-" * 50)

if __name__ == "__main__":
    test_chunker()
