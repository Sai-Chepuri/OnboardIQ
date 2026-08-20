---
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
