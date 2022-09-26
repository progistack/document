from odoo import fields, api, models, exceptions


class MailActivityInherit(models.Model):

    _inherit = 'mail.activity'
