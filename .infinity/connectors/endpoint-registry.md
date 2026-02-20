# Endpoint Registry — Infinity Orchestrator

> **Version:** 1.0.0  
> **Org:** Infinity-X-One-Systems  
> **Source of truth:** `.infinity/connectors/endpoint-registry.json`  
> Auto-maintained alongside infrastructure changes.

---

## Overview

This document provides a human-readable catalogue of all tool endpoints available to Infinity Orchestrator agents. Each entry maps to the corresponding machine-readable record in `endpoint-registry.json`. For auth details see [`auth-matrix.md`](./auth-matrix.md).

Status legend: ✅ active · 🔵 planned · ⚙️ conditional

---

## 🖥️ Local

Endpoints that resolve on the local runner or development machine.

| ID | Name | URL | Method | Auth | Status |
|----|------|-----|--------|------|--------|
| `local-health` | Local Health Check | `http://localhost:8080/health` | GET | none | ✅ |
| `local-api` | Local Orchestrator API | `http://localhost:8080/api/v1` | GET | bearer | ✅ |

---

## ☁️ Cloud

Cloud-hosted endpoints for the Infinity platform.

| ID | Name | URL | Method | Auth | Status |
|----|------|-----|--------|------|--------|
| `cloud-api-gateway` | Cloud API Gateway | `https://api.infinity-x-one.com/v1` | GET | bearer | 🔵 |

---

## 🌐 Cloudflare (Tunnel / Gateway / Access)

Cloudflare-protected ingress. All requests **must** carry Cloudflare Access service-token headers.

| ID | Name | URL | Method | Auth | Status | Notes |
|----|------|-----|--------|------|--------|-------|
| `cf-tunnel-orchestrator` | CF Tunnel — Orchestrator | `https://orchestrator.infinity-x-one.systems` | GET | cloudflare-access | 🔵 | Requires `CF_ACCESS_CLIENT_ID` + `CF_ACCESS_CLIENT_SECRET` headers |
| `cf-gateway` | CF Gateway Proxy | `https://gateway.infinity-x-one.systems/proxy` | POST | cloudflare-access | 🔵 | — |

---

## 🐳 Docker

Docker daemon and container management.

| ID | Name | URL | Method | Auth | Status | Notes |
|----|------|-----|--------|------|--------|-------|
| `docker-socket` | Docker Unix Socket | `unix:///var/run/docker.sock` | GET | unix-socket | ✅ | ⚠️ Security risk — use read-only mounts. See `docker-compose.singularity.yml`. |
| `docker-tcp` | Docker TCP API | `tcp://localhost:2375` | GET | tls-cert | ⚙️ | Only enabled with `DOCKER_TLS_VERIFY=1` and certs configured |

---

## ⚙️ GitHub Actions / Dispatch

GitHub API endpoints for workflow orchestration and dispatch.

| ID | Name | URL | Method | Auth | Correlation Header | Status |
|----|------|-----|--------|------|--------------------|--------|
| `gh-actions-dispatch` | Workflow Dispatch | `…/actions/workflows/{id}/dispatches` | POST | github-app-token | `X-GitHub-Delivery` | ✅ |
| `gh-repo-dispatch` | Repository Dispatch | `…/repos/{owner}/{repo}/dispatches` | POST | github-app-token | `X-GitHub-Delivery` | ✅ |
| `gh-actions-list-runs` | List Workflow Runs | `…/repos/{owner}/{repo}/actions/runs` | GET | github-app-token | — | ✅ |

> All GitHub API calls must include `X-GitHub-Api-Version: 2022-11-28`.

---

## 🤖 MCP (Model Context Protocol)

Server endpoints for AI agent tool-calling via MCP.

| ID | Name | URL | Method | Auth | Status |
|----|------|-----|--------|------|--------|
| `mcp-server-local` | MCP Server — Local | `http://localhost:3100/mcp` | POST | bearer | 🔵 |
| `mcp-server-cloud` | MCP Server — Cloud | `https://mcp.infinity-x-one.systems` | POST | bearer | 🔵 |

---

## 🔀 REST Gateway

Generic REST gateway for proxied external API calls.

| ID | Name | URL Pattern | Method | Auth | Audit Header | Status |
|----|------|-------------|--------|------|--------------|--------|
| `rest-gateway-v1` | REST Gateway v1 | `https://gateway.infinity-x-one.systems/rest/v1/{path}` | ANY | bearer | `X-Infinity-Correlation-ID` | 🔵 |

---

## 📥 Ingestion Pipeline

Data ingestion endpoints for streaming and batch workloads.

| ID | Name | URL | Method | Auth | Audit Header | Status |
|----|------|-----|--------|------|--------------|--------|
| `ingestion-event-stream` | Event Stream Ingest | `https://ingest.infinity-x-one.systems/events` | POST | bearer | `X-Infinity-Correlation-ID` | 🔵 |
| `ingestion-batch` | Batch Ingest | `https://ingest.infinity-x-one.systems/batch` | POST | bearer | — | 🔵 |

---

## 🗂️ Google Workspace Connector (Planned)

Google Workspace integration endpoints.

| ID | Name | URL | Method | Auth | Status |
|----|------|-----|--------|------|--------|
| `gws-gmail` | Gmail | `https://gmail.googleapis.com/gmail/v1/users/{userId}/messages` | GET | oauth2-google | 🔵 |
| `gws-drive` | Drive | `https://www.googleapis.com/drive/v3/files` | GET | oauth2-google | 🔵 |
| `gws-calendar` | Calendar | `https://www.googleapis.com/calendar/v3/calendars/{id}/events` | GET | oauth2-google | 🔵 |

---

## Correlation & Audit Headers

| Header | Purpose |
|--------|---------|
| `X-Infinity-Correlation-ID` | Unique request ID for distributed tracing; propagate across all service boundaries. |
| `X-Infinity-Session-ID` | Agent session identifier; attach to all calls within a single agent execution. |
| `X-GitHub-Delivery` | GitHub-assigned delivery GUID; present on all webhook and dispatch payloads. |

All endpoints that carry sensitive data **must** mask `Authorization`, `CF-Access-Client-Secret`, and `token` fields in logs. See `auth-matrix.md` for full masking requirements.
