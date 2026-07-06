---
id: C<n>
name: <slug>
producer: P<n>
consumers:
  P<n>: [<field-anchor>, ...]   # consumers declare which fields they read
  # the cascade engine uses these declarations
status: draft       # draft | locked
version: 0.1
---

# C<n> — <Name>

The `##` headings below are **stable field anchors** (slug of the heading text). Consumers reference these. Field-level cascade (decision 7) computes a diff over these field bodies.

## signature.<thing>
- input: `<type>`
- output: `<type>`
- raises: `<error>`

## behaviour.<thing>
- <one-line statement>
- <one-line statement>

## error.<class>
- <error semantics>
- <field on the error type if any>

## non_goals
- <explicit exclusion 1>
- <explicit exclusion 2>
