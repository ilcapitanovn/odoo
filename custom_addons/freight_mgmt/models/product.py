# -*- coding: utf-8 -*-

import logging
import re
from difflib import SequenceMatcher
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_default_exchange_rate(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        vnd_rate = vnd.rate if vnd else 0
        return float_round(vnd_rate, precision_digits=0)

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    def _get_default_list_price_vnd(self):
        vnd_price = 0.0
        if self.list_price and self.exchange_rate:
            vnd_price = self.list_price * self.exchange_rate
        return float_round(vnd_price, precision_digits=0)

    def _get_default_standard_price_vnd(self):
        vnd_standard_price = 0.0
        if self.standard_price and self.exchange_rate:
            vnd_standard_price = self.standard_price * self.exchange_rate
        return float_round(vnd_standard_price, precision_digits=0)

    port_loading_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Loading Port"
    )
    port_discharge_id = fields.Many2one(
        comodel_name="freight.catalog.port", string="Discharge Port"
    )
    container_id = fields.Many2one(
        comodel_name="freight.catalog.container", string="Container Type"
    )
    vessel_id = fields.Many2one(
        comodel_name="freight.catalog.vessel", string="Shipping Line"
    )
    is_no_vat = fields.Boolean(string="No Customer Taxes", default=False)

    exchange_rate = fields.Float(string='VND/USD rate', default=_get_default_exchange_rate, readonly=True,
                                 help='The rate of VND per USD.', tracking=True, store=True)

    product_currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id,
                                          tracking=True, required=True)
    vnd_currency_id = fields.Many2one('res.currency', 'Vietnamese Currency', compute="_compute_vnd_currency_id")
    list_price_vnd = fields.Float(
        'Sales Price (VND)', default=_get_default_list_price_vnd, tracking=True,
        digits='Product Price', help="Price at which the product is sold to customers in VND.",
    )
    standard_price_vnd = fields.Float(
        'Cost (VND)', default=_get_default_standard_price_vnd, tracking=True,
        digits='Product Price', groups="base.group_user",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the next unit that will leave the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")
    flag_just_updated = fields.Boolean(compute="_compute_flag_just_updated")

    def _compute_flag_just_updated(self):
        self.flag_just_updated = False

    def _compute_vnd_currency_id(self):
        vnd = self.env['res.currency'].sudo().search([('name', '=', 'VND')], limit=1)
        for rec in self:
            rec.vnd_currency_id = vnd.id or False

    @api.onchange('is_no_vat')
    def _onchange_is_no_vat(self):
        if self.is_no_vat:
            self.taxes_id = [(6, 0, [])]    # Mark empty if no vat

    @api.onchange('seller_ids')
    def _onchange_supplier_price(self):
        if not self.seller_ids:
            return

        if len(self.seller_ids) > 1:
            # variant_prices = self.mapped('seller_ids.price')
            # new_price = min(variant_prices)
            ''' Get the first supplier '''
            sorted_sellers = sorted(self.seller_ids, key=lambda x: x.sequence)
            new_price = sorted_sellers[0].price
        else:
            new_price = self.seller_ids.price

        if new_price > 0:
            self.standard_price = new_price

    @api.onchange('list_price')
    def _onchange_list_price(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.list_price_vnd = self.list_price * self.exchange_rate
            self.flag_just_updated = True

    @api.onchange('list_price_vnd')
    def _onchange_list_price_vnd(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.list_price = self.list_price_vnd / self.exchange_rate
            self.flag_just_updated = True

    @api.onchange('standard_price')
    def _onchange_standard_price(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.standard_price_vnd = self.standard_price * self.exchange_rate
            self.flag_just_updated = True

    @api.onchange('standard_price_vnd')
    def _onchange_standard_price_vnd(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.standard_price = self.standard_price_vnd / self.exchange_rate
            self.flag_just_updated = True

    def update_exchange_rate(self):
        self.ensure_one()
        self.exchange_rate = self._get_default_exchange_rate()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @api.model
    def _freight_mto_route(self):
        """MTO route record (env.ref ignores 'active', so it works even if
        the route is archived)."""
        return self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)

    @api.model
    def _freight_default_route_ids(self, with_mto=True):
        """Return the Buy (and optionally MTO) route ids."""
        xml_ids = ['purchase_stock.route_warehouse0_buy']
        if with_mto:
            xml_ids.insert(0, 'stock.route_warehouse0_mto')
        route_ids = []
        for xml_id in xml_ids:
            route = self.env.ref(xml_id, raise_if_not_found=False)
            if route:
                route_ids.append(route.id)
        return route_ids

    @api.model
    def _freight_normalize(self, text):
        """Lowercase and strip punctuation so names compare fairly."""
        return re.sub(r'[^\w\s]', ' ', (text or '').lower()).strip()

    @api.model
    def _freight_default_vendor_id(self, product_name=False):
        """Return the id of the vendor whose name is most similar to the
        product name, or False if nothing is similar enough.

        - Candidates are partners with supplier_rank > 0, pre-filtered by
          words of the product name (falls back to all vendors if no word
          matches).
        - Similarity = difflib ratio on normalized names. On a tie the first
          vendor (lowest id) wins.
        - Minimum similarity is read from system parameter
          'freight.vendor_match_threshold' (default 0.3).
        """
        if not product_name:
            return False

        """ Getting from the system parameter first, if not then getting by checking product name.
        Default vendor comes from a system parameter so it can be changed
        without code: Settings > Technical > System Parameters
        key = freight.default_vendor_id, value = partner id."""
        value = self.env['ir.config_parameter'].sudo().get_param(
            'freight.default_vendor_id')
        if value and value.isdigit():
            return int(value)

        Partner = self.env['res.partner'].sudo()
        base_domain = [('supplier_rank', '>', 0)]
        product_norm = self._freight_normalize(product_name)

        tokens = [t for t in product_norm.split() if len(t) >= 3]
        candidates = Partner.browse()
        if tokens:
            token_domain = []
            for token in tokens:
                token_domain = (['|'] if token_domain else []) + token_domain \
                               + [('name', 'ilike', token)]
            candidates = Partner.search(base_domain + token_domain, order='id')
        if not candidates:
            candidates = Partner.search(base_domain, order='id', limit=1000)

        threshold = float(self.env['ir.config_parameter'].sudo().get_param(
            'freight.vendor_match_threshold', 0.3))

        best_id, best_score = False, 0.0
        for partner in candidates:
            score = SequenceMatcher(
                None, product_norm,
                self._freight_normalize(partner.name)).ratio()
            if score > best_score:  # strict '>' keeps the first on ties
                best_id, best_score = partner.id, score
        return best_id if best_score >= threshold else False

    # ------------------------------------------------------------------
    # Defaults on create
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('purchase_ok', True):
                continue

            # 1. Vendor: best name match, only if none was given
            if not vals.get('seller_ids'):
                vendor_id = self._freight_default_vendor_id(vals.get('name'))
                if vendor_id:
                    vals['seller_ids'] = [(0, 0, {
                        'name': vendor_id,
                        'min_qty': 1.0,
                        'price': 0.0,
                    })]

            # 2. Routes: Buy always; MTO only when a vendor is present,
            #    otherwise the "MTO requires a vendor" constraint would block
            #    the creation of the product.
            route_ids = self._freight_default_route_ids(
                with_mto=bool(vals.get('seller_ids')))
            if route_ids and 'route_ids' not in vals:
                vals['route_ids'] = [(6, 0, route_ids)]
            elif route_ids:
                vals['route_ids'] = list(vals['route_ids']) + [
                    (4, rid) for rid in route_ids]
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Max one vendor in the Purchase tab
    # ------------------------------------------------------------------
    @api.constrains('seller_ids')
    def _check_single_vendor(self):
        if self.env.context.get('freight.skip_single_vendor'):
            return
        for template in self:
            if len(template.seller_ids) > 1:
                raise ValidationError(_(
                    "Product '%s' can only have one vendor. "
                    "Remove the current vendor before adding another.",
                    template.display_name))

    # ------------------------------------------------------------------
    # MTO requires a vendor
    # ------------------------------------------------------------------
    @api.constrains('route_ids', 'seller_ids')
    def _check_mto_requires_vendor(self):
        mto = self._freight_mto_route()
        if not mto:
            return
        for template in self:
            if mto in template.route_ids and not template.seller_ids:
                raise ValidationError(_(
                    "Product '%s' is set to Replenish on Order (MTO), so "
                    "its Purchase tab must have a vendor. Add a vendor or "
                    "disable MTO.", template.display_name))

    @api.onchange('route_ids', 'seller_ids')
    def _onchange_mto_requires_vendor(self):
        """Instant alert in the form, before the user tries to save."""
        mto = self._freight_mto_route()
        if mto and mto in self.route_ids and not self.seller_ids:
            return {'warning': {
                'title': _("Vendor required"),
                'message': _(
                    "Replenish on Order (MTO) is enabled, so a vendor is "
                    "required in the Purchase tab. Add a vendor or disable "
                    "MTO before saving."),
            }}

    # ------------------------------------------------------------------
    # Backfill for existing products (call from an automation / server action)
    # ------------------------------------------------------------------
    def action_freight_apply_mto_defaults_manually(self):
        """Fix existing Consumable products so that MTO, Buy and a vendor
        are all set.

        Server action code (Model: Product Template):
            records.action_freight_apply_mto_defaults_manually()
        or, to process every matching product regardless of selection:
            model.action_freight_apply_mto_defaults_manually()

        For each Consumable, purchasable product that is missing any of
        MTO, Buy or a vendor:
          - if the vendor list is empty, add the vendor whose name best
            matches the product name (same lookup as on creation);
          - tick whichever of MTO / Buy is missing.
        Everything is saved in one write so the "MTO requires a vendor"
        constraint sees the vendor and the routes together.

        If the product has no vendor and no similar vendor name is found,
        it is skipped entirely (MTO can't be valid without a vendor, and
        touching the routes of an MTO product with no vendor would trigger
        the constraint).

        Returns a dict {'updated': [ids], 'skipped': [ids]}.
        """
        mto = self._freight_mto_route()
        buy = self.env.ref('purchase_stock.route_warehouse0_buy',
                           raise_if_not_found=False)
        result = {'updated': [], 'skipped': []}
        required_routes = (mto | buy) if (mto and buy) else (mto or buy)
        if not required_routes:
            return result

        domain = [('type', '=', 'consu'), ('purchase_ok', '=', True)]
        templates = self.filtered_domain(domain) if self else self.search(domain)

        for template in templates:
            missing_routes = required_routes - template.route_ids
            missing_vendor = not template.seller_ids
            if not missing_routes and not missing_vendor:
                continue  # already correct

            vals = {}
            if missing_vendor:
                vendor_id = self._freight_default_vendor_id(template.name)
                if not vendor_id:
                    result['skipped'].append(template.id)
                    continue
                vals['seller_ids'] = [(0, 0, {
                    'name': vendor_id,
                    'min_qty': 1.0,
                    'price': 0.0,
                })]
            if missing_routes:
                vals['route_ids'] = [(4, rid) for rid in missing_routes.ids]
            template.write(vals)
            result['updated'].append(template.id)
        return result

    @api.model
    def action_automate_configure_mto_product(self):
        try:
            mto_route = self.env.ref('stock.route_warehouse0_mto', raise_if_not_found=False)
            buy_route = self.env.ref('purchase_stock.route_warehouse0_buy', raise_if_not_found=False)

            if not mto_route or not buy_route:
                raise UserError("Buy route or MTO route not found. Ensure the stock module is installed.")

            # Get the supplier (res.partner)
            default_supplier = self.env['res.partner'].search([('name', '=', 'VIETTOAN')], limit=1)
            if not default_supplier.exists():
                raise UserError("Default supplier [VIETTOAN] not found.")

            domain = [
                ('detailed_type', '=', 'consu')
            ]
            products = self.env['product.template'].sudo().search(domain)
            products_empty_routes = products.filtered(lambda p: not p.route_ids)
            products_missing_routes = products.filtered(
                lambda p: p.route_ids and (mto_route.id not in p.route_ids.ids or buy_route.id not in p.route_ids.ids)
            )

            count_empty_processed = 0
            for pro in products_empty_routes:
                if not pro.route_ids:
                    # Assign Buy and MTO route
                    obj = {'route_ids': [(4, buy_route.id), (4, mto_route.id)]}

                    # Make sure at least one seller is assigned
                    if not pro.seller_ids:
                        supplier_info = {
                            'name': default_supplier.id,
                            'company_id': self.env.company.id,
                            'product_tmpl_id': pro.id,
                            'price': pro.standard_price,
                            'min_qty': 0
                        }
                        obj['seller_ids'] = [(0, 0, supplier_info)]

                    pro.write(obj)
                    print(f"Empty Buy and MTO route assigned to product: {pro.name}")
                    count_empty_processed += 1

            count_missing_processed = 0
            for pro in products_missing_routes:
                obj = {}
                if mto_route.id not in pro.route_ids.ids and buy_route.id not in pro.route_ids.ids:
                    obj['route_ids'] = [(4, buy_route.id), (4, mto_route.id)]
                    print(f"Both missing Buy and MTO route assigned to product: {pro.name}")
                    count_empty_processed += 1
                elif mto_route.id not in pro.route_ids.ids:
                    obj['route_ids'] = [(4, mto_route.id)]
                    print(f"Missing MTO route assigned to product: {pro.name}")
                    count_missing_processed += 1
                elif buy_route.id not in pro.route_ids.ids:
                    obj['route_ids'] = [(4, buy_route.id)]
                    print(f"Missing Buy route assigned to product: {pro.name}")
                    count_missing_processed += 1

                # Make sure at least one seller is assigned
                if not pro.seller_ids:
                    supplier_info = {
                        'name': default_supplier.id,
                        'company_id': self.env.company.id,
                        'product_tmpl_id': pro.id,
                        'price': pro.standard_price,
                        'min_qty': 0
                    }
                    obj['seller_ids'] = [(0, 0, supplier_info)]

                if obj:
                    pro.write(obj)

            print(f"action_automate_configure_mto_product - executed successful. "
                  f"Empty products processed: {count_empty_processed}. "
                  f"Missing products processed: {count_missing_processed}")

        except Exception as e:
            _logger.exception("action_automate_configure_mto_product - Exception: " + str(e))


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    exchange_rate = fields.Float(related="product_tmpl_id.exchange_rate", string="VND/USD rate")
    price_vnd = fields.Float(
        'Price (VND)', compute='_compute_price_vnd', readonly=False, store=True, tracking=True,
        help="The price to purchase a product in VND")
    flag_just_updated = fields.Boolean(compute="_compute_flag_just_updated")

    def _compute_flag_just_updated(self):
        self.flag_just_updated = False

    @api.depends('price')
    def _compute_price_vnd(self):
        for rec in self:
            if rec.exchange_rate and not rec.flag_just_updated:
                rec.price_vnd = rec.price * rec.exchange_rate
                rec.flag_just_updated = True

    @api.onchange('price_vnd')
    def _onchange_price_vnd(self):
        if self.exchange_rate and not self.flag_just_updated:
            self.price = self.price_vnd / self.exchange_rate
            self.flag_just_updated = True


class ProductProduct(models.Model):
    _inherit = "product.product"
