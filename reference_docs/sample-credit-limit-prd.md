# PRD: Automated Credit Limit Enforcement

## Summary

Build an automated credit limit enforcement system that prevents B2B clients from exceeding their approved credit thresholds, reducing manual intervention by the finance team and cutting overdue receivables.

## Background & Context

Currently, credit limit checks are manual. Account managers verify limits in a spreadsheet before confirming shipments. This creates bottlenecks during peak season and has led to 3 cases of exceeded limits in Q1, totaling $120K in overdue receivables.

The finance team spends ~8 hours/week on credit monitoring. We also lose deals when the approval process takes >24 hours because clients go to competitors.

## Objective & Key Results

**Objective:** Reduce financial risk from credit overruns while maintaining booking speed.

**Key Results:**
- KR1: Zero credit limit breaches per quarter (from 3 in Q1)
- KR2: Credit check response time < 2 seconds (from avg 24 hours manual)
- KR3: Finance team time on credit monitoring reduced by 80%

## Target Users

**Primary:** Operations team processing bookings
- Pain: They can't confirm bookings without finance sign-off on credit
- Need: Instant, automated credit validation at booking time

**Secondary:** Finance team managing credit risk
- Pain: Manual monitoring is reactive, not preventive
- Need: Automated enforcement with override capabilities for edge cases

## Value Proposition

- Operations books faster (seconds vs. hours for credit approval)
- Finance shifts from monitoring to strategic credit decisions
- Company reduces overdue receivables and associated costs
- Clients get faster booking confirmations

## Solution

### Key Features

1. **Real-time credit check at booking** - System validates available credit before confirming a booking. Shows green/yellow/red status.
2. **Automated holds** - Bookings that exceed credit limits are held, not rejected. Client and ops are notified.
3. **Override workflow** - Finance can approve overrides with a reason. Creates an audit trail.
4. **Dashboard** - Real-time view of credit utilization across all accounts.

### UX Flow

Ops creates booking > System checks credit > If within limit, auto-approve > If exceeded, hold and notify > Finance reviews hold > Approve with override or reject

### Technical Notes

- Integrates with existing TMS via REST API
- Credit data sourced from ERP (SAP)
- Sub-second response required (cache credit limits locally, sync every 15 min)

## Assumptions & Risks

**Assumptions:**
- Credit limit data in SAP is accurate and up-to-date
- Ops team will adopt the new workflow without extensive retraining
- 15-minute sync interval is sufficient (no real-time changes needed)

**Risks:**
- ERP downtime could block all bookings (mitigation: cached fallback with 24hr TTL)
- Clients may push back on automated holds (mitigation: clear communication, fast override path)

## Release Plan

**Phase 1 (Week 1-3):** Real-time credit check + automated holds for top 20 accounts
**Phase 2 (Week 4-5):** Override workflow + dashboard
**Phase 3 (Week 6):** Roll out to all accounts + monitoring

**Success criteria for full launch:** Zero breaches in Phase 1 pilot, <5% false holds, override turnaround <1 hour.
