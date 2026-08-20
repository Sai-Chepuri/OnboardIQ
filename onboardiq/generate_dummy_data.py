import json
from pathlib import Path
from onboardiq.config import DATA_DIR

def generate_markdown_docs():
    """Generates standard Markdown API documentation."""
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
    print("Generated core Markdown API guide.")

def generate_notion_docs():
    """Generates a rich set of Notion Wiki documents containing RBAC tags and YAML metadata."""
    notion_path = DATA_DIR / "notion"
    notion_path.mkdir(exist_ok=True, parents=True)

    # 1. Onboarding Checklist
    onboarding = """---
Title: Engineering Onboarding Checklist
Author: Sarah Connor (Engineering Manager)
Status: Active
Created: 2026-01-10
Tags: [onboarding, team-eng, setup]
Access-Roles: [engineering, admin]
---
# Engineering Onboarding Checklist

Welcome to the team! Perform these Day 1 setup actions:
1. **VPN Access:** Request VPN access via IT portal (Ticket ID: `IT-VPN`).
2. **GitLab/GitHub:** Add SSH keys to GitHub and request to join `Company-Core-Engineers` organization.
3. **Local Dev Setup:** Initialize Docker containers using:
   ```bash
   make setup-dev
   ```
"""
    (notion_path / "engineering_onboarding.md").write_text(onboarding, encoding="utf-8")

    # 2. Database Decisions (PostgreSQL vs DynamoDB)
    adr = """---
Title: "ADR 004: Choice of PostgreSQL over DynamoDB for Transaction Records"
Author: David Miller (Principal Architect)
Status: Approved
Created: 2026-04-15
Tags: [architecture, databases, payments]
Access-Roles: [engineering, admin]
---
# Architecture Decision Record 004: Transaction Database Choice

## Context
We need to store transactional payment records with 100% ACID guarantees.

## Decision
We chose PostgreSQL because of relational transaction consistency requirements and key constraint validations.
If you encounter `relation transactions does not exist` errors, reset the local migration states via:
```bash
npm run db:reset
```
"""
    (notion_path / "adr_postgresql.md").write_text(adr, encoding="utf-8")

    # 3. Remote Work Policy
    remote = """---
Title: Global Remote Work Policy
Author: Jessica Taylor (VP of HR)
Status: Active
Created: 2026-02-01
Tags: [hr, remote, policy]
Access-Roles: [all]
---
# Global Remote Work Policy

Core collaboration hours for all teams are **10:00 AM to 3:00 PM EST**.
We provide a one-time home office setup stipend of **$500 USD** and a monthly internet stipend of **$50 USD** expensed via the HR portal.
"""
    (notion_path / "remote_work_policy.md").write_text(remote, encoding="utf-8")

    # 4. PTO Policy
    pto = """---
Title: Paid Time Off (PTO) and Leaves
Author: Jessica Taylor (VP of HR)
Status: Active
Created: 2026-02-05
Tags: [hr, pto, benefits]
Access-Roles: [all]
---
# Paid Time Off (PTO) and Leaves

* **Annual PTO Allocation:** 25 days per calendar year.
* **PTO Carry-Over:** Up to 5 unused days can carry over into the next year.
* **Parental Leave:** 16 weeks fully paid maternity leave; 8 weeks fully paid paternity leave.
"""
    (notion_path / "pto_policy.md").write_text(pto, encoding="utf-8")

    # 5. Coding Standards
    coding = """---
Title: Engineering Coding Standards and Quality Gates
Author: Sarah Connor (Engineering Manager)
Status: Active
Created: 2026-03-01
Tags: [engineering, guidelines, quality]
Access-Roles: [engineering, admin]
---
# Engineering Coding Standards

* **Test Coverage:** All pull requests must maintain at least **80% unit test coverage**.
* **Linting:** Standard checks are enforced via ESLint (TypeScript) and Black (Python).
* **Review Gate:** Every code change requires at least **two approved reviews** from senior team members.
"""
    (notion_path / "coding_standards.md").write_text(coding, encoding="utf-8")

    # 6. Git Workflow
    git = """---
Title: Git Branching Model and Pull Request Guidelines
Author: Sarah Connor (Engineering Manager)
Status: Active
Created: 2026-03-05
Tags: [engineering, git, workflow]
Access-Roles: [engineering, admin]
---
# Git Branching Model

We follow GitFlow guidelines:
* Main branches: `main` (production) and `develop` (staging).
* Feature branch prefix: `feature/` (e.g. `feature/checkout-routing`).
* All merges to `main` must use **Squash Merge** to maintain a linear history.
"""
    (notion_path / "git_workflow.md").write_text(git, encoding="utf-8")

    # 7. IT Equipment
    it = """---
Title: IT Equipment Provisioning and Request Guidelines
Author: Robert Chen (IT Manager)
Status: Active
Created: 2026-01-20
Tags: [it, equipment, reimbursement]
Access-Roles: [all]
---
# IT Equipment Provisioning

* **Standard Issue Laptop:** Apple MacBook Pro 16" (32GB RAM, 1TB SSD).
* **Peripherals:** Monitors and ergonomic chairs can be reimbursed up to **$300 USD** total.
* **Software Requests:** Submit software access forms (Slack, Zoom, JetBrains) via ServiceDesk Ticket ID `IT-EQUIP`.
"""
    (notion_path / "it_equipment_policy.md").write_text(it, encoding="utf-8")

    # 8. Performance Reviews
    perf = """---
Title: Performance Evaluation Cycle
Author: Jessica Taylor (VP of HR)
Status: Active
Created: 2026-02-15
Tags: [hr, reviews, performance]
Access-Roles: [all]
---
# Performance Evaluation Cycle

Reviews are conducted twice a year:
* **Q2 Review:** Self-assessment and manager review in June.
* **Q4 Review:** Full peer evaluation cycle in December.
* Ratings range from `1` (Needs Improvement) to `5` (Outstanding).
"""
    (notion_path / "performance_reviews.md").write_text(perf, encoding="utf-8")

    # 9. Code of Conduct
    coc = """---
Title: Corporate Code of Conduct
Author: HR Compliance Team
Status: Active
Created: 2026-01-05
Tags: [compliance, hr, policy]
Access-Roles: [all]
---
# Corporate Code of Conduct

We enforce a zero-tolerance policy for harassment, discrimination, or bullying.
Report any violations directly to `hr-escalations@company.com` or anonymously via compliance portal (Access Code: `COMP-SAFE`).
"""
    (notion_path / "code_of_conduct.md").write_text(coc, encoding="utf-8")
    
    print("Generated 9 Notion Wiki documents.")

def generate_confluence_docs():
    """Generates Confluence HTML documents with metadata headers and access roles."""
    conf_path = DATA_DIR / "confluence"
    conf_path.mkdir(exist_ok=True, parents=True)

    # 1. Release Runbook
    runbook = """<!DOCTYPE html>
<html>
<head>
    <title>Production Release & Deploy Runbook</title>
    <meta name="confluence-space" content="ENG">
    <meta name="confluence-page-id" content="8891023">
    <meta name="confluence-author" content="Marcus Vance">
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
    <h2>Deployment Schedule</h2>
    <p>We deploy using Kubernetes helm charts on Wednesdays at 06:00 UTC.</p>
</body>
</html>"""
    (conf_path / "release_runbook.html").write_text(runbook, encoding="utf-8")

    # 2. Disaster Recovery
    dr = """<!DOCTYPE html>
<html>
<head>
    <title>Multi-Region Disaster Recovery Plan</title>
    <meta name="confluence-space" content="OPS">
    <meta name="confluence-page-id" content="9912803">
    <meta name="confluence-author" content="Marcus Vance">
    <meta name="confluence-access-roles" content="ops,admin">
</head>
<body>
    <h1>Multi-Region Disaster Recovery Plan</h1>
    <h2>Region Configuration</h2>
    <ul>
        <li><strong>Primary Region:</strong> AWS <code>us-east-1</code> (N. Virginia)</li>
        <li><strong>Failover Region:</strong> AWS <code>ap-south-1</code> (Mumbai)</li>
    </ul>
    <h2>Target Metrics</h2>
    <p>Our PostgreSQL Aurora global database setup is configured with an RTO (Recovery Time Objective) of 5 minutes and an RPO (Recovery Point Objective) of 1 minute.</p>
</body>
</html>"""
    (conf_path / "disaster_recovery.html").write_text(dr, encoding="utf-8")

    # 3. AWS Networking Architecture
    aws_net = """<!DOCTYPE html>
<html>
<head>
    <title>AWS VPC and Subnet Routing Design</title>
    <meta name="confluence-space" content="OPS">
    <meta name="confluence-page-id" content="9922180">
    <meta name="confluence-author" content="Marcus Vance">
    <meta name="confluence-access-roles" content="ops,admin">
</head>
<body>
    <h1>AWS Network Subnets and Routing</h1>
    <p>The production VPC utilizes the IP block <code>10.100.0.0/16</code>.</p>
    <ul>
        <li>Public Subnets: <code>10.100.1.0/24</code> and <code>10.100.2.0/24</code></li>
        <li>Private Application Subnets: <code>10.100.10.0/24</code></li>
    </ul>
    <p>Static NAT Gateway IP attachments are <code>52.8.21.40</code> and <code>52.8.21.41</code>.</p>
</body>
</html>"""
    (conf_path / "aws_network_architecture.html").write_text(aws_net, encoding="utf-8")

    # 4. K8s Provisioning
    k8s = """<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Cluster Node Groups and Helm Upgrades</title>
    <meta name="confluence-space" content="OPS">
    <meta name="confluence-page-id" content="9922195">
    <meta name="confluence-author" content="Marcus Vance">
    <meta name="confluence-access-roles" content="ops,admin">
</head>
<body>
    <h1>EKS Cluster Provisioning Guide</h1>
    <p>Cluster Name: <code>prod-kube-cluster-01</code></p>
    <p>Standard Node groups run <code>m5.xlarge</code> instances. Autoscaling thresholds are set to a minimum of 3 and maximum of 15 instances.</p>
</body>
</html>"""
    (conf_path / "k8s_provisioning.html").write_text(k8s, encoding="utf-8")

    # 5. Redis Incident Post-mortem
    pm = """<!DOCTYPE html>
<html>
<head>
    <title>Incident Post-Mortem: Redis Outage (Incident #4821)</title>
    <meta name="confluence-space" content="ENG">
    <meta name="confluence-page-id" content="8821902">
    <meta name="confluence-author" content="Sarah Connor">
    <meta name="confluence-access-roles" content="engineering,ops,admin">
</head>
<body>
    <h1>Incident Post-Mortem: Redis Outage (#4821)</h1>
    <p><strong>Date:</strong> 2026-06-12</p>
    <p><strong>Root Cause:</strong> Memory exhaustion occurred on server <code>redis-prod-01</code> in the AP-South region due to unbounded key storage in checkout transactions logging.</p>
    <p><strong>Resolution:</strong> Enabled eviction policy <code>allkeys-lru</code> and set max memory cap to 4GB.</p>
</body>
</html>"""
    (conf_path / "incident_postmortem_redis.html").write_text(pm, encoding="utf-8")

    # 6. Global Travel Expenses
    travel = """<!DOCTYPE html>
<html>
<head>
    <title>Global Travel and Reimbursement Policies</title>
    <meta name="confluence-space" content="HR">
    <meta name="confluence-page-id" content="5512803">
    <meta name="confluence-author" content="Jessica Taylor">
    <meta name="confluence-access-roles" content="all">
</head>
<body>
    <h1>Global Travel Expense Reimbursement</h1>
    <h2>Accommodation Caps</h2>
    <ul>
        <li>Tier-1 Cities (New York, London, Tokyo): Maximum <strong>$250 USD</strong> per night.</li>
        <li>Tier-2 Cities: Maximum <strong>$150 USD</strong> per night.</li>
    </ul>
    <h2>Meal Allowances</h2>
    <p>Per Diem meal allowance is capped at <strong>$75 USD</strong> per day. Itemized receipts are mandatory for any individual expense exceeding $25.</p>
</body>
</html>"""
    (conf_path / "travel_expenses.html").write_text(travel, encoding="utf-8")

    # 7. Secrets Storage and IAM Manager
    secrets = """<!DOCTYPE html>
<html>
<head>
    <title>Secrets Storage and Credential Governance</title>
    <meta name="confluence-space" content="ENG">
    <meta name="confluence-page-id" content="8831902">
    <meta name="confluence-author" content="Sarah Connor">
    <meta name="confluence-access-roles" content="engineering,ops,admin">
</head>
<body>
    <h1>Secrets Storage Rules</h1>
    <p>All database credentials, API tokens, and private keys must be stored in AWS Secrets Manager under the path prefix <code>/prod/secrets/</code>.</p>
</body>
</html>"""
    (conf_path / "secrets_management.html").write_text(secrets, encoding="utf-8")
    
    print("Generated 7 Confluence HTML runbooks.")

def generate_slack_data():
    """Generates Slack channels and threads configuration with RBAC metadata."""
    slack_path = DATA_DIR / "slack"
    slack_path.mkdir(exist_ok=True, parents=True)

    users = {
        "U01A2B3C4D": {"real_name": "Alice Vance", "title": "Senior DevOps Lead", "name": "alice.v"},
        "U02E3F4G5H": {"real_name": "Sarah Connor", "title": "Engineering Manager", "name": "sarah.c"},
        "U03I4J5K6L": {"real_name": "John Doe", "title": "Junior Backend Engineer", "name": "john.d"},
        "U04M5N6O7P": {"real_name": "Robert Chen", "title": "IT Director", "name": "robert.c"}
    }

    # Channel 1: #deployment-ops
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

    # Channel 2: #general-announcements
    general_messages = [
        {
            "type": "message",
            "user": "U04M5N6O7P",
            "text": "Reminder: The deadline for submitting your Q4 health benefits enrollment details is November 30th. Please make sure your profiles are up to date on HRPortal.",
            "ts": "1782055600.000100"
        }
    ]

    # Channel 3: #dev-triage
    triage_messages = [
        {
            "type": "message",
            "user": "U03I4J5K6L",
            "text": "Staging checkout API is showing latency spikes up to 4.5 seconds. Anyone else seeing this?",
            "ts": "1782065600.000100",
            "reply_count": 2,
            "replies": [
                {"user": "U01A2B3C4D", "ts": "1782065650.000200"},
                {"user": "U03I4J5K6L", "ts": "1782065700.000300"}
            ]
        },
        {
            "type": "message",
            "user": "U01A2B3C4D",
            "text": "Yes, redis memory limits were reached. We need to clear the search query logs on redis-prod-01 to free up allocation.",
            "ts": "1782065650.000200",
            "thread_ts": "1782065600.000100"
        },
        {
            "type": "message",
            "user": "U03I4J5K6L",
            "text": "Understood, running cache clearing command. Latency is back down to 120ms.",
            "ts": "1782065700.000300",
            "thread_ts": "1782065600.000100"
        }
    ]

    # Channel 4: #security-alerts
    security_messages = [
        {
            "type": "message",
            "user": "U01A2B3C4D",
            "text": "IAM automated rotate-key task completed. Rotated access keys for service user `deploy-robot` successfully. Verify CI/CD pipeline builds are green.",
            "ts": "1782075600.000100"
        }
    ]

    channel_config = {
        "deployment-ops": {"access_roles": ["engineering", "ops", "admin"]},
        "general-announcements": {"access_roles": ["all"]},
        "dev-triage": {"access_roles": ["engineering", "ops", "admin"]},
        "security-alerts": {"access_roles": ["ops", "admin"]}
    }

    with open(slack_path / "users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    with open(slack_path / "deployment-ops.json", "w", encoding="utf-8") as f:
        json.dump(deployment_messages, f, indent=2)
    with open(slack_path / "general-announcements.json", "w", encoding="utf-8") as f:
        json.dump(general_messages, f, indent=2)
    with open(slack_path / "dev-triage.json", "w", encoding="utf-8") as f:
        json.dump(triage_messages, f, indent=2)
    with open(slack_path / "security-alerts.json", "w", encoding="utf-8") as f:
        json.dump(security_messages, f, indent=2)
    with open(slack_path / "channels_config.json", "w", encoding="utf-8") as f:
        json.dump(channel_config, f, indent=2)
        
    print("Generated Slack channels, user maps, and channel configs.")

def run():
    print("Generating expanded corporate documentation dataset...")
    generate_markdown_docs()
    generate_notion_docs()
    generate_confluence_docs()
    generate_slack_data()
    print("All diverse mock documentation generated successfully in /data.")

if __name__ == "__main__":
    run()
