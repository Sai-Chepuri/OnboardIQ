---
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
