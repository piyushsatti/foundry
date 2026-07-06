# SOC2 Access Control Readiness Checklist

## 1. Purpose

This checklist tracks our readiness for the access-control portion of an upcoming
SOC2 Type II audit. It covers provisioning, deprovisioning, periodic access review,
privileged access, exception handling, and evidence collection for every in-scope
system (production infrastructure, the customer data warehouse, and internal admin
tools).

## 2. Scope

In scope: all systems that store, process, or grant access to customer data or
production infrastructure, whether accessed by employees, contractors, or automated
service accounts. Systems integrated with the corporate identity provider (Okta) and
systems with local, non-federated accounts (a small number of legacy on-prem tools)
are both in scope.

## 3. Provisioning

- [ ] New hire onboarding: access is requested via the IT ticketing system, approved
  by the hiring manager, and provisioned by IT within 1 business day of start date.
  Owner: IT Operations.
- [ ] Contractor onboarding: access is requested by the sponsoring manager, approved
  by IT Security, time-boxed to the contract end date by default, and automatically
  flagged for review if the contract is extended. Owner: IT Security.
- [ ] Internal transfer / role change: the employee's manager and the new team's
  manager jointly confirm the target access profile; prior role's access not needed
  in the new role is removed within 5 business days. Owner: IT Operations.

## 4. Deprovisioning

- [ ] Employee termination: IT disables the employee's SSO account within 4 hours of
  the termination being recorded in the HR system, and a full access revocation
  (including any local, non-federated accounts) is completed within 24 hours. Owner:
  IT Operations.
- [ ] Contractor offboarding: access expires automatically at the contract end date
  recorded in the vendor management system; the sponsoring manager is notified 5
  days before expiry to confirm no extension is needed. Owner: IT Security.
- [ ] Involuntary termination: HR notifies IT Security directly (bypassing the
  standard ticket queue) for same-hour access revocation. Owner: IT Security.

## 5. Periodic access review

- [ ] Quarterly access reviews are performed for every in-scope system, including
  systems integrated with Okta and the small number of local-account legacy tools,
  by exporting each system's own user list and having the relevant manager attest to
  continued need for access. Owner: IT Security, coordinated with system owners for
  local-account tools.
- [ ] Any account not attested to within the review window is disabled pending
  manager follow-up. Owner: IT Security.

## 6. Privileged access

- [ ] All administrative/privileged accounts require MFA. Owner: IT Security.
- [ ] Privileged sessions (production infrastructure admin, database admin) time out
  after 15 minutes of inactivity and require re-authentication. Owner: Platform
  Engineering.
- [ ] Privileged account credentials (service account keys, shared admin passwords)
  are rotated every 90 days. Owner: Platform Engineering.
- [ ] Break-glass emergency-access accounts are logged separately and reviewed by IT
  Security within 24 hours of any use. Owner: IT Security.

## 7. Logging and monitoring

- [ ] All access grants, revocations, and privileged actions are written to an
  append-only audit log. Owner: Platform Engineering.
- [ ] Access-request justifications are free-text fields supplied by the requester;
  these are stored as plain text in the audit log and displayed as plain text
  (escaped, not rendered as HTML) in the internal review dashboard. Owner: Platform
  Engineering.
- [ ] Audit logs are retained for 1 year and access to the logs themselves is
  restricted to IT Security and the compliance team. Owner: IT Security.

## 8. Exceptions

- [ ] Temporary access exceptions (e.g., short-term elevated access for an incident)
  may be granted for a documented business need, time-boxed to a maximum of 7 days,
  and require approval from the requester's manager and IT Security. IT Security
  owns tracking all open exceptions and ensuring each one expires or is renewed
  explicitly; a weekly report of open exceptions is reviewed at the IT Security
  standup. Owner: IT Security.

## 9. Evidence collection

- [ ] Quarterly access review evidence (exports, manager attestations) is collected
  by IT Security using an internally built export script with read-only access to
  the identity provider's reporting API. Owner: IT Security.
- [ ] Exported user-access reports (names, roles, system entitlements) are stored in
  an access-restricted evidence folder limited to IT Security, the compliance team,
  and designated auditors, not in a general-purpose shared drive. Owner: IT
  Security.
- [ ] Evidence is retained for the audit period plus one year per the record
  retention policy. Owner: Compliance.

## 10. Open items

- Confirm whether the legacy on-prem tools' local accounts can be migrated to Okta
  before the audit window opens, which would simplify the review process in
  Section 5.
- Confirm retention period alignment between the audit log policy (Section 7) and
  the general record retention policy (Section 9).
