from odoo import fields, api, models, _
from odoo.exceptions import UserError


class DocumentHistorical(models.Model):

    _name = 'document.historical'
    _rec_name = 'reference'
    _order = 'create_date desc'

    reference = fields.Char(_("Reference"))
    document_id = fields.Many2one('document.document', string=_("Courrier lié"))
    partner_id = fields.Many2one('res.partner', string=_("Émetteur"))
    company_id = fields.Many2one('res.company', string=_('Société destinataire'))
    description = fields.Html(_("Description"))
    next_historical = fields.Many2one('document.historical', _("Modification suivante"))
    previous_historical = fields.Many2one('document.historical', _("Modification precedente"))
    is_restored = fields.Boolean()

    def get_previous_document_historical(self):
        if self.previous_historical:
            action = {
                'name': 'Historique précedente',
                'res_model': 'document.historical',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('document.document_historical_form').id,
                'res_id': self.previous_historical.id
            }
            return action
        else:
            print("else")
            raise UserError(_("Cette historique est la prémière sauvegarde qui a été faite!"))

    def get_next_document_historical(self):
        if self.next_historical:
            action = {
                'name': 'Historique suivante',
                'res_model': 'document.historical',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('document.document_historical_form').id,
                'res_id': self.next_historical.id
            }
            return action
        else:
            raise UserError(_("Cette historique est la dernière sauvegarde qui a été faite!"))

    def restore_document_historical(self):
        print("Test", self)
        document = self.env['document.document'].browse(self.document_id.id)
        if document:
            document.write({
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'description': self.description,
                'restored_historical': self.id
            })
            self.is_restored = 1
            action = {
                'name': "Historique restaurée",
                'type': "ir.actions.act_window",
                'res_model': 'document.document',
                'view_mode': 'form',
                'view_id': self.env.ref('document.view_document_form').id,
                'views': [(self.env.ref('document.view_document_form').id, 'form')],
                'res_id': document.id
            }

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _(f"L'historique {self.reference} à bien été restaurée."),
                    'next': action
                }
            }
        else:
            print("Jamais executé")


class ResponseHistorical(models.Model):

    _name = 'response.historical'
    _rec_name = 'reference'

    def _compute_reference(self):
        historical = self.env['response.historical'].search([('response', '=', self.document_id.id)])
        self.reference = f"RES/HIS/{len(historical)+1}"
    reference = fields.Char(_("Reference"), compute='_compute_reference')
    response_id = fields.Many2one('document.response', string=_("Courrier sortant lié"))
    partner_id = fields.Many2one('res.partner', string=_("Destinataire"))
    company_id = fields.Many2one('res.company', string=_("Societé émetrice"))
    body = fields.Html(_("Corps"))
