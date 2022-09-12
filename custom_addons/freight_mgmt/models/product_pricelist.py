# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def action_view_product_pricelist(self):
        self.ensure_one()
        # pricelist_id = self.env.context.get('active_id', False)
        pricelist_id = self.id
        pricelist_name = self.display_name

        domain = [('pricelist_id', '=', pricelist_id)]

        pricelist_tree = self.env.ref('freight_mgmt.freight_product_pricelist_item_tree_view', False)
        view_id_tree = self.env['ir.ui.view'].search([('name', '=', "freight.product.pricelist.item.tree")])
        return {
            'name': pricelist_name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id_tree[0].id, 'tree')],
            'view_id': pricelist_tree.id,
            'target': 'main',
            'domain': domain,
        }


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    port_loading_id = fields.Many2one(related="product_tmpl_id.port_loading_id", string="Loading Port", store=True)
    port_discharge_id = fields.Many2one(related="product_tmpl_id.port_discharge_id", string="Discharge Port", store=True)
    container_id = fields.Many2one(related="product_tmpl_id.container_id", string="Container Type", store=True)
    vessel_id = fields.Many2one(related="product_tmpl_id.vessel_id", string="Line", store=True)

    type = fields.Selection(related="product_tmpl_id.type")
