# Copyright 2019 Vicent Cubells <vicent.cubells@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _update_picking_invoices(self):
        self.ensure_one()
        purchase = self.invoice_line_ids.mapped('purchase_line_id.order_id')
        if not purchase:
            return
        self.mapped('invoice_line_ids.move_line_ids').filtered(
            lambda x: x.state == 'done'
            and not x.location_dest_id.scrap_location
            and x.location_id.usage == 'supplier').mapped(
                'picking_id').write({'invoice_ids': [(4, self.id)]})

    @api.model
    def create(self, values):
        invoice = super().create(values)
        invoice._update_picking_invoices()
        return invoice

    @api.multi
    def _prepare_invoice_line_from_po_line(self, line):
        vals = super()._prepare_invoice_line_from_po_line(line)
        moves = self.env['stock.move'].search([
            ('purchase_line_id', '=', line.id),
        ])
        move_ids = moves._get_moves()
        vals['move_line_ids'] = [(6, 0, move_ids.ids)]
        return vals


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.model
    def create(self, vals):
        line = super().create(vals)
        if not line.purchase_line_id:
            return line
        moves = self.env['stock.move'].search([
            ('purchase_line_id', '=', line.purchase_line_id.id),
        ])
        move_ids = moves._get_moves()
        move_ids.write({'invoice_line_id': line.id})
        return line
