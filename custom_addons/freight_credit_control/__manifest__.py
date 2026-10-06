# -*- coding: utf-8 -*-
{
    'name': "Freight Credit Control Tower",
    'version': '15.0.1.0.0',
    'summary': "Credit hold, BOD approval and release workflow for Freight Bookings",
    'description': """
Freight Credit Control Tower
=============================
Adds a financial hold / release workflow on top of Freight Management (freight_mgmt):

* Automatically flags confirmed bookings as "Blocked" when the customer has
  crossed their credit Blocking Amount (reuses base_accounting_kit's
  Warning/Blocking Amount fields on res.partner).
* Sales can request a BOD (Board of Directors) approval to release a blocked
  shipment, with a note (e.g. "Customer promised wire transfer by 5 PM").
  Change: this is a temporary/manual override, not a change to the credit
  policy itself.
* BOD / Finance can Approve or Reject the release request from a dedicated
  Kanban "Control Tower" board (Blocked / Pending Approval / Ready to Release).
* Once released (or never blocked), Delivery Order can be printed; otherwise
  the system prevents it.
* A single Control Tower screen: the 4 KPI cards are rendered as a banner
  (same core mechanism Odoo's own Accounting/Sales dashboards use) directly
  above the Kanban board - one screen, one action, no separate dashboard page.
    """,
    'author': 'VietToanERP',
    'website': 'https://www.viet-toan.com',
    'category': 'Inventory/Delivery',
    'depends': ['freight_mgmt', 'base_accounting_kit', 'sale', 'account', 'mail'],
    'data': [
        'security/freight_credit_control_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'wizard/freight_credit_release_wizard_views.xml',
        'views/freight_credit_banner_templates.xml',
        'views/freight_booking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
