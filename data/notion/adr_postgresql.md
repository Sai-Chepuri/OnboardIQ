---
Title: ADR 004: Choice of PostgreSQL over DynamoDB for Transaction Records
Author: David Miller (Principal Architect)
Status: Approved
Created: 2026-04-15
Tags: [architecture, databases, payments]
---

# Architecture Decision Record 004: DB Storage for Payments

## Context and Problem Statement
We need to store transactional payment records with 100% ACID guarantees. Transaction volumes are projected to reach 10 million transactions per month.

## Decision Drivers
* ACID compliance is non-negotiable.
* Complex joint queries are required for end-of-month accounting.
* Support for transactional locks.

## Considered Options
1. **Amazon DynamoDB:** Highly scalable, but lacks complex native joins and requires multi-table design.
2. **PostgreSQL (RDS Multi-AZ):** Relational, strong ACID compliance, great SQL support for reporting.

## Decision Outcome
We chose **PostgreSQL** because payment operations require atomic transactions across multiple balance tables (Debit vs Credit). DynamoDB's eventual consistency and lack of native reporting joins would increase engineering complexity.
