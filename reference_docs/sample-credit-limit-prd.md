# PRD: Client credit limit and accounting system integration

> _Sample reference document for writing-style matching only. Fictional B2B freight context; contains no company-specific data._

## Overview
Improve the integration between a B2B freight forwarding platform and its accounting system to enable holistic client credit management. This system will unify invoicing, payment tracking, credit/debit note handling, and credit limit evaluation into a single source of truth for customer financial health.

## Goals
- Provide real-time visibility into each customer's credit position
- Automate the sync of invoicing and payment data between the platform and the accounting system
- Enable credit limit assignment, enforcement, and revision workflows
- Reduce manual reconciliation effort between the platform and the accounting system

## Non-goals
- Replacing the accounting system as the system of record for accounting
- Automating credit limit decisions (this is a decision-support tool, not auto-approval)

---

## Component 1: Invoice portion

Tracks the full lifecycle of each invoice and all adjustments made against it.

### Data points
| Field | Description | Source |
|-------|-------------|--------|
| Invoice ID | Unique identifier synced from accounting system | Accounting system |
| Invoice value | Original billed amount | Accounting system |
| Payments applied | Payments received and matched against this invoice | Accounting system |
| Credit notes (invoice-level) | Credit memos applied/adjusted against this specific invoice | Accounting system |
| Debit notes (invoice-level) | Debit memos applied/adjusted against this specific invoice | Accounting system |
| Invoice revisions | Any amendments to the original invoice value or line items | Accounting system / App |

### Calculated fields
- **Net invoice outstanding** = Invoice value - Payments applied - Credit notes adjusted + Debit notes adjusted (accounting for revisions)

### Key considerations
- Invoices may be partially paid; the system must track partial payment application
- Revisions to invoices should maintain an audit trail (original value, revised value, reason, timestamp)
- Credit and debit notes at the invoice level must be distinguished from customer-level notes (see Component 2)

---

## Component 2: Customer level balances

Tracks credits, debits, and payments at the customer level that have NOT yet been adjusted against a specific invoice.

### Data points
| Field | Description | Source |
|-------|-------------|--------|
| Unadjusted advances/payments | Payments or deposits made by the customer not yet applied to an invoice | Accounting system |
| Customer-level credit notes | Credit memos issued to the customer not tied to a specific invoice | Accounting system |
| Customer-level debit notes | Debit memos issued to the customer not tied to a specific invoice | Accounting system |

### Key considerations
- In the accounting system, credit memos can exist at the customer level without being associated to any invoice. These sit as open credits on the customer's account and can be applied to future invoices or refunded.
- Unadjusted advances should be flagged for reconciliation -- they represent customer funds held on account
- The system should surface aging of unadjusted items (e.g., "Sample Client has a $5,000 unapplied credit note from 45 days ago")

---

## Component 3: Customer credit evaluation

Manages the documentation, assignment, and governance of credit limits for each client.

### Workflow
1. **Documentation** -- Collect required financial documents from the client (e.g., bank references, trade references, financial statements)
2. **Credit limit assignment** -- Based on evaluation, assign a credit limit amount to the customer
3. **Validity period** -- Each credit limit has an effective date and expiry date
4. **Revision** -- Credit limits can be revised (up or down) based on payment behavior, changed business conditions, or periodic review

### Data points
| Field | Description |
|-------|-------------|
| Credit limit amount | Maximum outstanding balance allowed for this customer |
| Effective date | When this credit limit takes effect |
| Expiry date | When this credit limit expires and must be reviewed |
| Supporting documents | Uploaded references and financial documents |
| Approval status | Pending / Approved / Rejected / Under review |
| Revision history | Log of all changes to the credit limit with reasons |

### Key considerations
- Credit limits should trigger alerts before expiry (e.g., 30 days before)
- Revision requests should follow an approval workflow (who can request, who can approve)
- Historical credit limit data should be retained for audit purposes

---

## Component 4: Customer credit limit (the combined view)

This is the final, holistic output that combines all three components above into a single customer credit position.

### Formula

```
Customer credit exposure =
    Sum of all outstanding invoices (net of payments and adjustments at invoice level)
  + Debit notes issued at customer level
  - Credit notes issued at customer level
  - Unadjusted advances/payments
```

### Credit limit status

```
Available credit = Assigned credit limit - Customer credit exposure
```

| Status | Condition |
|--------|-----------|
| Within limit | Available credit > 0 |
| Near limit | Available credit < configurable threshold (e.g., 10% of assigned limit) |
| Over limit | Available credit < 0 |
| Expired | Credit limit past expiry date |

### Business rules
- When a customer is **over limit**, new shipment bookings should be flagged/blocked (configurable per customer)
- When a customer is **near limit**, an alert should be sent to the account manager and finance team
- When a credit limit is **expired**, treat as zero limit until renewed
- Dashboard should provide a real-time view of all customers' credit positions

---

## Sync architecture (accounting system integration)

### Direction of data flow
- **Accounting system -> App**: Invoice data, payment records, credit/debit memos, customer balances
- **App -> Accounting system**: (Future) Credit limit status, hold flags

### Sync frequency
- To be determined: real-time webhook vs. scheduled polling (recommend starting with scheduled polling every 15-30 minutes, with option to move to webhooks)

### Error handling
- Failed syncs should be logged and retried
- Data discrepancies between app and accounting system should surface in a reconciliation dashboard

---

## Open questions
- What approval workflow is needed for credit limit assignment and revision? (Single approver vs. multi-level?)
- Should shipment bookings be blocked when over limit, or just warned? Is this configurable per customer?
- What is the desired sync frequency with the accounting system?
- Are there existing credit policies or documentation templates to incorporate?
- How should customers with multiple sub-entities in the accounting system be handled?

---

## Success metrics
- Reduction in time spent on manual credit checks before booking
- Reduction in overdue receivables from customers exceeding their credit limit
- Percentage of customers with active, non-expired credit limits
- Sync reliability (% successful syncs with accounting system)
