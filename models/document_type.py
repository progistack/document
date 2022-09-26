from datetime import date
from odoo import api, fields, models


class VehicleType(models.Model):
    _name = "document.type"
    _description = "Type de document"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Type", required=True)
    active = fields.Boolean(string="Active", default=True)
