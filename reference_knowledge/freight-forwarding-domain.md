# Freight Domain Knowledge for Product Managers

> This file is injected as domain context when generating logistics and freight forwarding PM artifacts. It provides operationally accurate knowledge so generated PRDs reflect how freight forwarding actually works on the ground.

---

## Part 1: The Macro Logistics Framework

Logistics manages the lifecycle of a product from raw material to final customer delivery. Freight forwarding is the general contractor handling the complex, cross-border transportation leg.

### Key operational areas
- **Procurement and Sourcing** — purchase orders, supplier lead times, inbound schedules
- **Warehouse Management** — cross-docking, slotting, WMS systems
- **Inventory Optimization** — safety stock, ABC classification, reorder point logic
- **Order Fulfillment** — batch/zone/wave picking, pack-out accuracy
- **Distribution and Last-Mile** — routing algorithms, empty miles reduction (last mile is the most expensive per unit)

---

## Part 2: Freight Forwarding Execution

### Stage 1: Quotation and Booking

The shipper issues a Request for Quote (RFQ). The forwarder calculates total **landed cost**:
- **Base freight rate** (ocean, air, or rail)
- **BAF** — Bunker Adjustment Factor (fuel surcharge)
- **CAF** — Currency Adjustment Factor
- **THC** — Terminal Handling Charges
- **PSS** — Peak Season Surcharge
- **ETS** — Emissions Trading System charges (increasingly common in EU lanes)
- **Port and documentation fees**

The forwarder's margin = **sell rate** (charged to client) minus **buy rate** (paid to carrier/NVOCC).

**Rate types:**
- **Spot rate** — one-time, no commitment. Higher price.
- **Contract rate** — negotiated for defined period and volume. Lower price, guaranteed capacity.

**Speed requirement:** Any feature in the quoting path must add no more than 2-3 seconds to the workflow. Rate intelligence API calls typically respond in under 1 second.

### Stage 2: Cargo Pickup and Consolidation

**Container types and pricing implications:**

| Type | Use case | Pricing note |
|------|----------|-------------|
| 20' dry (TEU) | Standard cargo, base unit | Base rate unit |
| 40' dry (FEU) | Standard cargo, higher volume | Typically 1.5-1.8x a 20' rate, not 2x |
| 40' High Cube (HC) | Tall or voluminous cargo | Slight premium over standard 40' |
| 20'/40' Reefer | Temperature-controlled (perishables, pharma) | Significant premium + power supply fees |
| Open Top / Flat Rack | Oversized or heavy machinery | Priced per case, often breakbulk rates |

**LCL vs FCL:**
- **LCL** (Less-than-Container Load) — priced per CBM or weight ton, whichever is greater
- **FCL** (Full Container Load) — priced per container regardless of fill level
- Consolidation combines multiple shippers' LCL cargo into one FCL to reduce per-unit costs

### Stage 3: Export Customs Clearance

Required documentation:
- **Commercial Invoice** — value, quantity, buyer/seller. Determines customs duties.
- **Packing List** — itemized contents by weight and volume
- **Certificate of Origin (COO)** — proves manufacturing origin, affects tariff rates
- **Export permits** — required for controlled goods (dual-use tech, hazmat, sanctioned destinations)
- **ISF (Importer Security Filing)** — required by US CBP 24 hours before vessel departure for US-bound cargo. Missing this triggers **$5,000+ fine per violation** and potential cargo holds.

A single missing document or incorrect HS code can trigger:
- Cargo holds at port
- **Demurrage charges** — fees for cargo sitting at a port/terminal beyond free time
- **Detention charges** — fees for keeping a container beyond allotted free time after pickup
- Regulatory penalties

### Stage 4: Main Carriage and Milestone Tracking

**BOL hierarchy:**
- **MBL (Master Bill of Lading)** — issued by ocean carrier (Maersk, MSC, CMA CGM) to the forwarder. Controls physical cargo release.
- **HBL (House Bill of Lading)** — issued by forwarder to the shipper (their client). Carrier does not see the HBL.
- This two-layer structure enables consolidation — multiple shippers under one MBL.

**Shipment milestones:**
1. Departed origin port
2. Transshipment (if not direct — cargo moves between vessels at a hub port)
3. Arrived destination port
4. Customs hold (if triggered)
5. Cleared customs
6. Out for delivery
7. Delivered / POD (Proof of Delivery)

Tracking data comes from carrier APIs, AIS vessel data, or platforms like Project44 and FourKites. Modern systems trigger **exception-based alerts** when a shipment deviates from its expected timeline.

### Stage 5: Import Customs and Final Delivery

Import duties calculated on:
- HS classification code
- Declared value on commercial invoice
- Country of origin (trade agreements may reduce/eliminate duties)
- Whether anti-dumping duties apply

---

## Part 3: Documentation and Financial Workflows

### The Document Stack

| Document | Issued by | Purpose | Risk if missing |
|----------|-----------|---------|-----------------|
| House BOL (HBL) | Forwarder to shipper | Receipt of goods, contract of carriage | Shipper cannot claim cargo |
| Master BOL (MBL) | Carrier to forwarder | Carrier's contract, controls physical cargo release | Cargo stranded at port |
| Commercial Invoice | Shipper | Value declaration for customs | Customs hold, incorrect duty calculation |
| Packing List | Shipper | Weight/volume/contents detail | Inspection delays |
| Certificate of Origin | Chamber of Commerce | Proves manufacturing origin | Loss of preferential tariff rates |
| ISF (US-bound) | Forwarder or broker | US security filing | $5,000+ fine per violation |
| Arrival Notice | Carrier/forwarder | Alerts consignee of arrival | Missed free time, demurrage charges |

### Financial Reconciliation

**Cost capture:** Tariffs, fuel surcharges, port fees, inland haulage, and customs duties are captured as the shipment progresses. Each cost line ties to a specific shipment event.

**Revenue recognition:** AR triggers an invoice when a container hits a "Cleared Customs" or "Delivered" milestone — reducing payment friction and accelerating cash flow.

**Credit exposure formula:**
```
Customer credit exposure =
    Sum of all outstanding invoices (net of payments and adjustments)
  + Debit notes issued at customer level
  - Credit notes issued at customer level
  - Unadjusted advances/payments

Available credit = Assigned credit limit - Customer credit exposure
```

**Accounting system sync architecture:**
- Direction: Accounting system (QuickBooks/Xero/SAP) is source of truth for payments; forwarding app is source of truth for shipment-linked charges
- Sync frequency: Scheduled polling (15-30 min) vs. webhooks. Polling is simpler; webhooks faster but harder to debug.
- Failure handling: Failed syncs must be logged, retried, and surfaced in a reconciliation dashboard
- Partial payments: Invoices can be partially paid; the system must track partial application

---

## Part 4: Key Integrations Map

| System | Purpose | Examples | Data flow |
|--------|---------|----------|-----------|
| TMS | Core operational platform | CargoWise, Magaya, custom builds | Bidirectional hub |
| Ocean carriers | Booking, tracking, BOL | Maersk, MSC, CMA CGM, Hapag-Lloyd | Booking out, tracking events in |
| NVOCCs | Buy rates, consolidation | Shipco, Allseas, Vanguard | Rates in, booking requests out |
| Rate intelligence | Market benchmarking | Xeneta, Freightos Baltic Index | Rate queries out, market data in |
| Accounting | Invoicing, payments, credit | QuickBooks, Xero, SAP | Invoices out, payments in |
| Carrier tracking | Real-time visibility | Project44, FourKites, INTTRA | Events in, status queries out |
| Customs / compliance | Filing, classification | US CBP ABI, single-window systems | Filings out, clearance status in |
| CRM | Client management | Salesforce, HubSpot | Client data bidirectional |

---

## Part 5: Incoterms (2020)

Incoterms define where cost and risk transfer from seller to buyer — they directly affect which party the forwarder bills for which legs of transport.

| Term | Risk transfers at | Seller pays for | Common in |
|------|-------------------|-----------------|-----------|
| EXW (Ex Works) | Seller's premises | Nothing beyond making goods available | Domestic, buyer-controlled supply chains |
| FCA (Free Carrier) | Named place of delivery | Delivery to carrier at origin | Growing alternative to FOB for containers |
| FOB (Free On Board) | Ship's rail at origin port | Inland transport + export clearance | Most common for ocean freight |
| CIF (Cost, Insurance, Freight) | Ship's rail at origin (cost paid further) | Freight + insurance to destination port | Common when seller controls shipping |
| DAP (Delivered at Place) | Named destination (before unloading) | All transport to destination | E-commerce, door-to-door |
| DDP (Delivered Duty Paid) | Buyer's premises | Everything including import duties | Maximum seller obligation |

**Why this matters for PMs:** Incoterms determine which cost lines appear on which party's invoice. A feature that generates quotes must know the Incoterm to calculate which charges to include.

---

## Part 6: Domain-Specific PM Considerations

When writing specs or PRDs for logistics features, always address:

1. **Data sync direction and source of truth** — Which system owns which data? The forwarding app owns shipment data; accounting system owns payment data. Conflicts need a reconciliation workflow, not a silent overwrite.

2. **Speed constraints** — Quoting is time-sensitive. Any feature in the quoting path must add minimal latency (<3 seconds). Carrier booking APIs can be slow; design for async confirmation.

3. **Multi-party data flows** — A single shipment involves shipper, consignee, carrier, customs broker, port authority, and forwarder. Every feature should map which parties produce and consume which data.

4. **Compliance as a hard requirement** — Customs regulations, trade sanctions, Incoterms obligations, and ISF filing deadlines are not "nice to have." A missed ISF filing is $5,000+. A wrong HS code is a customs hold. Treat compliance as blocking, not advisory.

5. **Financial exposure and credit risk** — Features touching money need explicit handling of: credit limits, payment terms, currency conversion, partial payments, and cascading effects of over-limit clients on booking flows.

6. **Demurrage and detention economics** — Delays are expensive. Demurrage (port/terminal fees) and detention (container fees) accrue daily. Features affecting cargo velocity should quantify the cost of delays.

7. **Audit trails** — Regulated industry. Every change to a BOL, invoice, credit limit, or customs filing needs a who/when/why log. Audit is not phase-2; it ships with v1.

8. **Fallback behavior** — When an API (carrier, rate provider, accounting system) is down, what does the user see? Define graceful degradation: cached rates, manual override, queued sync retry.

9. **Document-driven workflows** — Many logistics processes are blocked until a specific document is received, signed, or filed. Model document state (draft, submitted, accepted, rejected) as a first-class entity.

10. **Exception handling over happy-path tracking** — Ops teams don't need dashboards for shipments going smoothly. They need systems that surface exceptions: customs holds, missed vessels, document discrepancies, credit limit breaches. Design for the unhappy path first.
