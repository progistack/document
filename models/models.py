# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InheritMailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def action_send_mail(self):
        """ Used for action button that do not accept arguments. """
        self._action_send_mail(auto_commit=False)
        response = self.env['document.response'].sudo().search([('id', '=', self.env.context['active_id'])], limit=1)
        response.write({"state": "2_send", 'send_mail': True})
        return {'type': 'ir.actions.act_window_close'}


class InheritAccountAnalytic(models.Model):
    _inherit = 'account.analytic.account'

    response_count = fields.Integer(compute="_compute_response", string='Compteur réponse', copy=False, default=0,
                                    store=True)
    response_ids = fields.One2many('document.response', 'project_id', string="Sortants")

    @api.depends("response_ids")
    def _compute_response(self):
        for rec in self:
            rec.response_count = len(rec.response_ids.ids)

    def action_return_document(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "document.response",
            "domain": [('project_id', '=', self.id)],
            "name": "Sortants",
            'view_mode': 'kanban,tree,form',
        }
        return result


class InheritPartner(models.Model):
    _inherit = 'res.partner'

    response_count = fields.Integer(compute="_compute_response", string='Compteur réponse', copy=False, default=0,
                                    store=True)
    response_ids = fields.One2many('document.response', 'partner_id', string="Sortants")

    @api.depends("response_ids")
    def _compute_response(self):
        for rec in self:
            rec.response_count = len(rec.response_ids.ids)

    def action_return_document(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "document.response",
            "domain": [('partner_id', '=', self.id)],
            "name": "Sortants",
            'view_mode': 'kanban,tree,form',
        }
        return result
