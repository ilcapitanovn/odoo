# Copyright 2022 Bao Thinh Software - Tuan Huynh
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2.extensions import AsIs

from odoo import api, fields, models, tools


class SaleProfitForwarderAnalysisReport(models.Model):
    _name = "sale.profit.forwarder.analysis.report"
    _description = "Sale Profit Forwarder Analysis Report"
    _auto = False
    _rec_name = "bill_id"

    @api.model
    def _get_selection_invoice_state(self):
        return self.env["account.move"].fields_get(allfields=["state"])["state"][
            "selection"
        ]

    # invoice_state = fields.Selection(
    #     selection="_get_selection_invoice_state", string="Invoice Status", readonly=True
    # )

    company_id = fields.Many2one("res.company", "Company", readonly=True)
    customer_id = fields.Many2one("res.partner", "Customer", readonly=True)
    user_id = fields.Many2one("res.users", "Sale User", readonly=True)
    sale_partner_id = fields.Many2one("res.partner", "Sale", readonly=True)
    sale_order_id = fields.Many2one("sale.order", "Sale Order", readonly=True)
    purchase_order_id = fields.Many2one("purchase.order", "Purchase Order", readonly=True)
    booking_id = fields.Many2one("freight.booking", "Booking", readonly=True)
    bill_id = fields.Many2one("freight.billing", "Bill", readonly=True)
    pod_id = fields.Many2one("freight.catalog.port", "POL/D", readonly=True)
    line_id = fields.Many2one("freight.catalog.vessel", "Line", readonly=True)

    # date_invoice = fields.Date("Date Invoice", readonly=True)
    bill_no = fields.Char("BILL NO", readonly=True)
    volumes = fields.Char("CONT", readonly=True)
    etd = fields.Date("ETD", readonly=True)
    order_type = fields.Char("Freehand <br/>or <br/>Nominated", readonly=True)
    date_order = fields.Date("Date Order", readonly=True)

    po_amount_untaxed = fields.Float("Chua VAT (I)", readonly=True)
    po_amount_total = fields.Float("Co VAT (I)", readonly=True)
    po_amount_tax = fields.Float("VAT (I)", readonly=True)

    so_amount_untaxed = fields.Float("Chua VAT (O)", readonly=True)
    so_amount_total = fields.Float("Co VAT (O)", readonly=True)
    so_amount_tax = fields.Float("VAT (O)", readonly=True)

    cost_no_vat = fields.Float("Chi phi (ko hd)", readonly=True)
    revenue_no_vat = fields.Float("Doanh thu dv (ko hd)", readonly=True)

    so_commission_total = fields.Float("USD (COM KH)", readonly=True)
    so_commission_total_vnd = fields.Float(compute="_compute_so_commission_in_vnd", string="VND (COM KH)")
    po_commission_total = fields.Float("USD (COM LINE)", readonly=True)
    po_commission_total_vnd = fields.Float(compute="_compute_po_commission_in_vnd", string="VND (COM LINE)")

    margin = fields.Float("Margin", readonly=True)

    profit_before_tax_no_vat = fields.Float(compute="_compute_profits", readonly=True)
    profit_before_tax_vat = fields.Float(compute="_compute_profits", readonly=True)
    vat_payable = fields.Float(compute="_compute_profits", readonly=True)
    business_tax_amount = fields.Float(compute="_compute_profits", readonly=True)
    profit_after_tax_no_vat = fields.Float(compute="_compute_profits", readonly=True)
    profit_after_tax_vat = fields.Float(compute="_compute_profits", readonly=True)

    display_pod = fields.Char(compute="_compute_display_pod", readonly=True)
    display_sale_name = fields.Char(compute="_compute_display_sale_name", readonly=True)
    display_cus = fields.Char(compute="_compute_display_cus", readonly=True)
    display_line = fields.Char(compute="_compute_display_line", readonly=True)

    # invoice_line_id = fields.Many2one(
    #     "account.move.line", "Invoice line", readonly=True
    # )
    # commission_id = fields.Many2one("sale.commission", "Sale commission", readonly=True)

    @api.depends('so_amount_untaxed', 'margin')
    def _compute_profits(self):
        for rec in self:
            rec.profit_before_tax_no_vat = rec.so_amount_untaxed - rec.po_amount_untaxed
            rec.profit_before_tax_vat = rec.margin
            rec.vat_payable = rec.so_amount_tax - rec.po_amount_tax
            rec.business_tax_amount = rec.profit_before_tax_no_vat * 0.2
            rec.profit_after_tax_no_vat = rec.profit_before_tax_no_vat - rec.vat_payable - rec.business_tax_amount
            rec.profit_after_tax_vat = rec.profit_before_tax_vat - rec.vat_payable - rec.business_tax_amount

    @api.depends('pod_id')
    def _compute_display_pod(self):
        for record in self:
            display_pod = record.pod_id.name if record.pod_id else ''
            record.display_pod = display_pod

    @api.depends('sale_partner_id')
    def _compute_display_sale_name(self):
        for record in self:
            display_name = ''
            if record.sale_partner_id and record.sale_partner_id.display_name:
                arr = record.sale_partner_id.display_name.split()
                display_name = arr[len(arr)-1]
            record.display_sale_name = display_name

    @api.depends('customer_id')
    def _compute_display_cus(self):
        for record in self:
            display_cus = record.customer_id.name if record.customer_id else ''
            # record.display_cus = display_cus[0:3]
            record.display_cus = display_cus.split()[0]

    @api.depends('line_id')
    def _compute_display_line(self):
        for record in self:
            display_line = record.line_id.name if record.line_id else ''
            # record.display_line = display_line[0:3]
            if display_line:
                record.display_line = display_line.split()[0]
            else:
                record.display_line = ''

    @api.depends('so_commission_total')
    def _compute_so_commission_in_vnd(self):
        usd = self.env['res.currency'].search([('name', '=', 'USD')])
        vnd = self.env['res.currency'].search([('name', '=', 'VND')])
        now = fields.Datetime.now()

        for record in self:
            amount_vnd = usd._convert(record.so_commission_total, vnd, record.company_id, now)
            record.so_commission_total_vnd = amount_vnd

    @api.depends('po_commission_total')
    def _compute_po_commission_in_vnd(self):
        usd = self.env['res.currency'].search([('name', '=', 'USD')])
        vnd = self.env['res.currency'].search([('name', '=', 'VND')])
        now = fields.Datetime.now()

        for record in self:
            amount_vnd = usd._convert(record.po_commission_total, vnd, record.company_id, now)
            record.po_commission_total_vnd = amount_vnd

    def _select(self):
        select_str = """
            SELECT
            fbl.id AS id,
            fbl.id AS bill_id,
            fbl.booking_id AS booking_id,
            fbl.partner_id AS customer_id,
            fbl.company_id AS company_id,
            fbl.user_id AS user_id,
            usale.partner_id AS sale_partner_id,
            fbl.order_id AS sale_order_id,
            po.id AS purchase_order_id,
            fbk.port_discharge_id AS pod_id,
            fbk.vessel_id AS line_id,
            
            fbl.vessel_bol_number AS bill_no,
            '' AS volumes,
            DATE(fbk.etd_revised) AS etd,
            CASE WHEN so.order_type IS NULL THEN 'freehand' ELSE so.order_type END AS order_type,
            so.date_order AS date_order,
            
            po.amount_untaxed AS po_amount_untaxed,
            po.amount_total AS po_amount_total,
            po.amount_tax AS po_amount_tax,
            
            so.amount_untaxed AS so_amount_untaxed,
            so.amount_total AS so_amount_total,
            so.amount_tax AS so_amount_tax,
            
            0 AS cost_no_vat,
            0 AS revenue_no_vat,
            
            po.commission_total AS po_commission_total,
            so.commission_total AS so_commission_total,
            so.margin
        """
        return select_str

    def _from(self):
        from_str = """
            freight_billing fbl
            INNER JOIN freight_booking fbk ON fbk.id = fbl.booking_id
            LEFT JOIN res_partner cus ON cus.id = fbl.partner_id
            LEFT JOIN freight_catalog_port pod ON fbk.port_discharge_id = pod.id
            LEFT JOIN freight_catalog_vessel fline ON fbk.vessel_id = fline.id
            LEFT JOIN res_users usale ON usale.id = fbl.user_id
            INNER JOIN res_partner psale ON usale.partner_id = psale.id
            LEFT JOIN sale_order so ON fbl.order_id = so.id
            LEFT JOIN purchase_order po on so.name = po.origin
        """
        return from_str

    # def _group_by(self):
    #     group_by_str = """
    #         GROUP BY ai.partner_id,
    #         ai.state,
    #         ai.date,
    #         ail.company_id,
    #         rp.id,
    #         pt.categ_id,
    #         ail.product_id,
    #         pt.uom_id,
    #         ail.id,
    #         aila.settled,
    #         aila.commission_id
    #     """
    #     return group_by_str

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s FROM ( %s ) )",
            (
                AsIs(self._table),
                AsIs(self._select()),
                AsIs(self._from()),
                # AsIs(self._group_by()),
            ),
        )
