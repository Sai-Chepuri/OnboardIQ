import json
from pathlib import Path
from onboardiq.config import DATA_DIR

def generate_markdown_docs():
    """Generates standard Markdown API documentation."""
    # Tagging with Access Roles: ["engineering", "ops", "admin"]
    content = """# Payment Gateway API Integration Guide
Access-Roles: [engineering, ops, admin]

This document describes how to integrate the Core Payment Gateway into internal services.

## Base URL
The staging and production endpoints are:
* **Staging:** `https://api.staging.payments.company.com/v2`
* **Production:** `https://api.payments.company.com/v2`

## Authentication
All API requests must include the API key in the request headers:
```http
Authorization: Bearer sec_key_live_abcdef123456
```

> [!WARNING]
> Never commit live API keys to Git. Use Secret Manager to retrieve keys at runtime.

## Endpoints

### 1. Create a Payment Intent
Create a payment session to accept checkout transactions.

* **HTTP Method:** `POST`
* **Path:** `/payment-intents`
* **Request Body:**
| Field | Type | Description | Required |
|---|---|---|---|
| `amount` | integer | Amount in cents (e.g. 1000 for $10.00) | Yes |
| `currency` | string | ISO 4-letter currency code (e.g. `USD`) | Yes |
| `idempotency_key` | string | Unique UUID to prevent double-charging | Yes |
"""
    (DATA_DIR / "markdown" / "payment_gateway.md").write_text(content, encoding="utf-8")
    print("Generated Markdown documentation with RBAC tags.")

def generate_notion_docs():
    """Generates Notion-style Markdown exports with YAML properties containing RBAC metadata."""
    onboarding_content = """---
Title: Engineering Onboarding Checklist
Author: Sarah Connor (Engineering Manager)
Status: Active
Created: 2026-01-10
Tags: [onboarding, team-eng, setup]
Access-Roles: [engineering, admin]
---

# Engineering Onboarding Checklist

Welcome to the Engineering team! This page outlines your tasks for your first two weeks.

## Day 1: Machine Setup
1. **VPN Access:** Request access to the company VPN via IT Help Desk portal (ServiceDesk Ticket ID: `IT-VPN`).
2. **GitLab/GitHub:** Add your SSH key to GitHub and request to join the `Company-Core-Engineers` organization.
3. **Environment:** Run the local dev script to pull Docker containers:
   ```bash
   make setup-dev
   ```
"""

    adr_content = """---
Title: "ADR 004: Choice of PostgreSQL over DynamoDB for Transaction Records"
Author: David Miller (Principal Architect)
Status: Approved
Created: 2026-04-15
Tags: [architecture, databases, payments]
Access-Roles: [engineering, admin]
---

# Architecture Decision Record 004: DB Storage for Payments

## Context and Problem Statement
We need to store transactional payment records with 100% ACID guarantees.
"""
    (DATA_DIR / "notion" / "engineering_onboarding.md").write_text(onboarding_content, encoding="utf-8")
    (DATA_DIR / "notion" / "adr_postgresql.md").write_text(adr_content, encoding="utf-8")
    print("Generated Notion simulated files with RBAC tags.")

def generate_confluence_docs():
    """Generates Confluence HTML exports containing Confluence metadata and RBAC tags."""
    # Tagging with Access Roles: ["ops", "admin"]
    runbook_html = """<!DOCTYPE html>
<html>
<head>
    <title>Production Release & Deploy Runbook</title>
    <meta name="confluence-space" content="ENG">
    <meta name="confluence-page-id" content="8891023">
    <meta name="confluence-author" content="Marcus Vance">
    <meta name="confluence-last-modified" content="2026-07-15">
    <meta name="confluence-access-roles" content="ops,admin">
</head>
<body>
    <h1>Production Release & Deploy Runbook</h1>
    <div class="confluence-information-macro confluence-information-macro-warning">
        <p class="title">CRITICAL REQUIREMENT</p>
        <div class="confluence-information-macro-body">
            Never deploy to production without an approved Pull Request and a green build in Jenkins.
        </div>
    </div>
    
    <h2>Deployment Steps</h2>
    <p>We deploy using Kubernetes helm charts on Wednesdays at 06:00 UTC.</p>
</body>
</html>
"""
    (DATA_DIR / "confluence" / "release_runbook.html").write_text(runbook_html, encoding="utf-8")
    print("Generated Confluence simulated HTML files with RBAC tags.")

def generate_slack_data():
    """Generates simulated Slack export files with channel configuration defining access roles."""
    users = {
        "U01A2B3C4D": {
            "real_name": "Alice Vance",
            "title": "Senior DevOps Lead",
            "name": "alice.v"
        },
        "U02E3F4G5H": {
            "real_name": "Sarah Connor",
            "title": "Engineering Manager",
            "name": "sarah.c"
        },
        "U03I4J5K6L": {
            "real_name": "John Doe",
            "title": "Junior Backend Engineer",
            "name": "john.d"
        }
    }
    
    # Slack messages in deployment-ops channel (RBAC Roles: ["engineering", "ops", "admin"])
    deployment_messages = [
        {
            "client_msg_id": "m1",
            "type": "message",
            "user": "U03I4J5K6L",
            "text": "Hey team, I'm trying to run the payment gateway locally, but I get database connection errors. Anybody know what's going on?",
            "ts": "1782045600.000100",
            "reply_count": 3,
            "replies": [
                {"user": "U01A2B3C4D", "ts": "1782045650.000200"},
                {"user": "U03I4J5K6L", "ts": "1782045700.000300"},
                {"user": "U01A2B3C4D", "ts": "1782045800.000400"}
            ]
        },
        {
            "type": "message",
            "user": "U01A2B3C4D",
            "text": "Hey <@U03I4J5K6L>, did you run the migrations? Usually you need to run `npm run db:migrate` before the app starts.",
            "ts": "1782045650.000200",
            "thread_ts": "1782045600.000100"
        },
        {
            "type": "message",
            "user": "U03I4J5K6L",
            "text": "Thanks <@U01A2B3C4D>! Yes, I tried that but I get `relation transactions does not exist`. Did something change in the schema?",
            "ts": "1782045700.000300",
            "thread_ts": "1782045600.000100"
        },
        {
            "type": "message",
            "user": "U01A2B3C4D",
            "text": "Ah, yes. David merged ADR 004 yesterday. You need to reset the dev database first by running `npm run db:reset` because we modified the primary key constraint on transactions.",
            "ts": "1782045800.000400",
            "thread_ts": "1782045600.000100"
        }
    ]

    # Map channel config with access roles
    channel_config = {
        "deployment-ops": {
            "access_roles": ["engineering", "ops", "admin"]
        }
    }

    with open(DATA_DIR / "slack" / "users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
        
    with open(DATA_DIR / "slack" / "deployment-ops.json", "w", encoding="utf-8") as f:
        json.dump(deployment_messages, f, indent=2)
        
    with open(DATA_DIR / "slack" / "channels_config.json", "w", encoding="utf-8") as f:
        json.dump(channel_config, f, indent=2)
        
    print("Generated Slack simulated JSON data and channels config with RBAC tags.")

def run():
    print("Generating simulated corporate knowledge dataset...")
    generate_markdown_docs()
    generate_notion_docs()
    generate_confluence_docs()
    generate_slack_data()
    print("All mock documentation generated in /data.")

if __name__ == "__main__":
    run()
