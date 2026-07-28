---
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
