---
Title: Engineering Onboarding Checklist
Author: Sarah Connor (Engineering Manager)
Status: Active
Created: 2026-01-10
Tags: [onboarding, team-eng, setup]
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

## Week 1: Environment Bootstrapping
* Ask team lead for access to Doppler for local environment variables.
* Run the initial migration on the local database:
   ```bash
   npm run db:migrate
   ```
* If you run into `ERR_CONN_REFUSED` on port `5432`, ensure your Docker container `postgres-db` is running by checking `docker ps`.
