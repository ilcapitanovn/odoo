# Freight MTO Auto PO Sub-Products (Odoo 15)

## Install
1. Copy `freight_mto_auto_subproducts` into your addons path.
2. Apps > Update Apps List > install "Freight MTO Auto PO Sub-Products".

## Use
Product > Purchase tab > "MTO Auto PO Sub-Products": add lines
(Sub-Product, Vendor override, Default Qty, Notes, Active, drag to reorder).

When a "Buy" procurement (MTO from a confirmed SO) creates a PO line for the
product, one line per active sub-product is added:
- qty = Default Qty x main line qty (converted to the product's own UoM);
  sub-product UoM = its purchase UoM
- price = vendor pricelist of the sub-product for the PO vendor (0 if none)
- no vendor override (or same vendor as the PO) -> same PO
- different vendor -> separate draft PO for that vendor (same origin,
  flagged "Auto Sub-Products PO"); reused if one already exists
- if Odoo merges extra demand into an existing main line, the sub-lines are
  increased by the matching amount
- generated lines are flagged (`is_mto_auto_line`, `mto_parent_line_id`) and
  stay fully editable. Later SO/PO edits do not re-sync.

## Assumptions to verify against freight_mgmt
- MTO purchases go through `stock.rule._run_buy` (Replenish on Order + Buy).
  Service-to-purchase (`sale_purchase`) is not covered.
- Product A stays on the PO as its own line.
- Reordering-rule (orderpoint) replenishments are not expanded.
- Nested sub-products are blocked.
