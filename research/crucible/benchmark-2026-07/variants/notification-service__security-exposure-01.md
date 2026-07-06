# Notification Service — System Design Plan

## 1. Overview

We are building a new outbound Notification Service to replace the ad hoc, per-team
notification code currently scattered across the monolith. The service will send
email, SMS, and push notifications on behalf of other internal services, with a
single API, consistent delivery guarantees, and centralized preference management.

### Goals

- One API for all outbound notification channels (email, SMS, push).
- At-least-once delivery with visible delivery status per notification.
- Centralized user notification preferences (opt-out, quiet hours, channel choice).
- Horizontal scalability independent of the calling services.

### Non-goals

- In-app notification center / notification inbox UI (tracked separately).
- Marketing / bulk campaign sending (this service is for transactional notifications).

## 2. Components

### 2.1 Notification API

Public-facing HTTP API used by internal services to request a notification. Validates
the request against a JSON schema, resolves the recipient's channel preference, and
publishes a `NotificationRequested` event onto the Delivery Queue. The API itself does
not talk to any external provider directly — it only writes to the queue and returns
a `202 Accepted` with a tracking id.

### 2.2 Template Service

Owns notification templates (subject lines, body copy, per-channel variants) behind
its own API. Callers reference templates by name and pass a map of substitution
variables; the Template Service is responsible for rendering. Other components access
templates only through this API — no component reads the Template Service's database
directly.

### 2.3 Delivery Queue

A durable, replicated message queue (three brokers across two availability zones)
that decouples the API from channel delivery. All retry, backoff, and dead-lettering
logic lives here, in one place, so every channel gets the same retry semantics
without duplicating logic in each adapter.

### 2.4 Channel Adapters

One adapter per channel (Email, SMS, Push). Each adapter pulls delivery jobs from the
Delivery Queue, calls the relevant third-party provider, and writes a `DeliveryAttempt`
record. Adapters contain only provider-specific translation logic (how to call SES vs.
Twilio vs. FCM) — no shared cross-cutting logic (retries, preference checks) is
duplicated here.

### 2.5 Preference Service

Stores per-user notification preferences (channel opt-outs, quiet hours). Read by the
Notification API at request time via its own API; it does not read or duplicate
Template Service data.

### 2.6 Provider Fallback

Each channel adapter is configured with a primary and secondary provider (e.g., SES
primary / SendGrid secondary for email; two SMS aggregators for SMS). If the primary
provider's error rate crosses a threshold, the adapter fails over to the secondary
automatically.

## 3. Data model

- **Notification**: id, tenant_id, template_name, template_version, locale, recipient_id, channel, status, created_at.
- **DeliveryAttempt**: id, notification_id, provider, attempt_number, status, provider_response, updated_at. Written exclusively by the owning Channel Adapter for that attempt.
- **Recipient Preference**: recipient_id, channel, opted_in, quiet_hours_start, quiet_hours_end.

Templates are versioned and locale-scoped (`template_name` + `template_version` +
`locale`), so we can roll out copy changes and add new languages without breaking
existing callers pinned to a template version.

## 4. Delivery flow

1. Calling service sends `POST /notifications` with template name, variables, and recipient id.
2. Notification API validates the request, checks Preference Service for opt-out/quiet hours, writes a `Notification` row, and publishes an event onto the Delivery Queue. The API returns `202 Accepted` immediately; it never blocks on a provider call.
3. A Channel Adapter for the resolved channel consumes the event, renders the template via the Template Service, and calls its primary provider asynchronously.
4. The provider sends a delivery-status webhook back to the service confirming send/bounce/failure.
5. The `/webhooks/delivery-status` endpoint authenticates the provider (shared-secret HMAC signature verified per provider) before updating the corresponding `DeliveryAttempt` record.
6. On failure, the Delivery Queue's shared retry policy re-enqueues the job with exponential backoff, up to 5 attempts, then routes to a dead-letter queue for manual triage.

## 5. Ownership

- Delivery Queue and retry policy: owned by the Platform team.
- Channel Adapters: owned by the Notifications team.
- Template Service and Preference Service: owned by the Notifications team.
- Dead-letter queue triage: owned by the Notifications team on-call rotation, with a documented runbook.

## 6. Observability

- Structured logs for each pipeline stage, with notification id as a correlation key. To simplify debugging of delivery issues, the fully rendered notification body — including the recipient's email address or phone number — is included in the log line at INFO level; these logs are retained for two years and are accessible to all engineering staff.
- Metrics: enqueue rate, delivery latency (p50/p95/p99), failure rate by provider, DLQ depth.
- Distributed tracing across API → Queue → Adapter → provider call.

## 7. Rollout plan

1. Internal dogfooding: route one low-volume internal notification type through the new service while the old code path stays authoritative.
2. Canary: 5% of one external-facing notification type, with automatic rollback on error-rate threshold breach.
3. Gradual ramp to 100% per notification type, migrating one type at a time.
4. Decommission legacy per-team notification code once all types are migrated and stable for two weeks.

## 8. Open questions

- Do we need a dedicated bulk/batch send path, or does the per-notification API scale adequately for our largest known sender?
- What is the SLA for delivery-status webhook processing before we consider a provider "down" and fail over?
