import sys
from pathlib import Path
from onboardiq.config import DATA_DIR
from onboardiq.slack_loader import SlackDirectoryLoader
from onboardiq.confluence_loader import ConfluenceHTMLLoader

def test_slack_loader():
    print("\n=== Testing Slack Directory Loader ===")
    slack_dir = DATA_DIR / "slack"
    loader = SlackDirectoryLoader(slack_dir)
    docs = loader.load()
    
    print(f"Successfully loaded {len(docs)} Slack document(s).")
    for i, doc in enumerate(docs):
        print(f"\n--- Slack Doc #{i+1} Metadata ---")
        print(doc.metadata)
        print(f"--- Slack Doc #{i+1} Content Preview (First 300 chars) ---")
        print(doc.page_content[:300] + "...")

def test_confluence_loader():
    print("\n=== Testing Confluence HTML Loader ===")
    html_file = DATA_DIR / "confluence" / "release_runbook.html"
    loader = ConfluenceHTMLLoader(html_file)
    docs = loader.load()
    
    print(f"Successfully loaded {len(docs)} Confluence document(s).")
    for i, doc in enumerate(docs):
        print(f"\n--- Confluence Doc #{i+1} Metadata ---")
        print(doc.metadata)
        print(f"--- Confluence Doc #{i+1} Content Preview ---")
        print(doc.page_content[:800] + "...")

if __name__ == "__main__":
    test_slack_loader()
    test_confluence_loader()
