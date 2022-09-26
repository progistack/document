# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, http, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class Response(models.Model):
    _name = 'document.response'
    _description = 'Response.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'
    _rec_name = "reference"

    @api.depends('company_id')
    def _compute_company_adress(self):
        # print("self.company_id.partner_id.address", self.company_id.partner_id.city)
        adresse = [self.company_id.partner_id.street,
                   self.company_id.partner_id.city, self.company_id.partner_id.zip]
        ad = "{}\n{} {}".format(
            self.company_id.partner_id.street,
            self.company_id.partner_id.city,
            self.company_id.partner_id.zip)
        # print(ad)
        self.company_adress = ad

    def _get_default_project(self):
        project = self.env['account.analytic.account'].search([('name', '=', 'Autre')])
        return project.id

    def _set_company_list(self):
        print("Avat selection", self)
        company_ids = self.env['res.company'].sudo().search([])
        selection = []
        for company_id in company_ids:
            selection.append((str(company_id.id), company_id.name))

        print("Selection", selection)
        return selection

    def person_name(self):

        user_writer = self.env.user.name
        name = str(user_writer).split(' ')
        abrv = ""
        for i in name:
            abr = i[0].capitalize()
            abrv += abr
        ref_user = f"/{abrv}/MJ"

        return ref_user

    def write_ref(self):
        x = datetime.now()
        date = x.strftime("%d/%m/%Y")
        abr = self.env.company.abbreviation
        abr_company = f"{date}/{abr}"
        return abr_company

    # def new_reference(self):
    #     sequence = self.reference
    #     print(sequence)
    #     date = self.date
    #     print(date)
    #     abr_company = self.abr_company
    #     print(abr_company)
    #     user_writer = self.env.user.name
    #     print(user_writer)
    #     ref = f"{date}/{abr_company}/{sequence}/{user_writer}/J.M"
    #     print(ref)
    #     return ref

    # def new_reference(self):
    #
    #     user_writer = self.env.user.name
    #     name = str(user_writer).split(' ')
    #     abrv = ""
    #     for i in name:
    #         abr = i[0].capitalize()
    #         abrv += abr
    #     ref_user = f"{abrv}/MJ"
    #     x = datetime.now()
    #     date = x.strftime("%d/%m/%Y")
    #     abr = self.env.company.abbreviation
    #     abr_company = f"{date}/{abr}/"
    #     sequence = self.reference
    #     ref = f"{abr_company}/{sequence}/{ref_user}"
    #
    #     return ref

    reference = fields.Char(string='Référence', required=True, copy=False, readonly=True, index=True,
                            default=lambda self: _('New'))
    department_ids = fields.Many2many('hr.department', string="Départements", required=True)
    document_id = fields.Many2one('document.document', string="Courrier")
    project_id = fields.Many2one('account.analytic.account', string="Projet", track_visibility='onchange',
                                 default=_get_default_project)
    partner_id = fields.Many2one('res.partner', string="Destinataire", tracking=True)
    subject = fields.Char('Objet', track_visibility='onchange')
    email = fields.Char("Email contact")
    body = fields.Html('Corps du sortant', readonly=False, tracking=True, track_visibility='onchange')
    active = fields.Boolean(string="Active", default=True)
    send_mail = fields.Boolean(string="Envoyé", default=False)
    company_id = fields.Many2one('res.company', string="Societé émettrice")
    company_id_selection = fields.Selection(_set_company_list, 'Société émettrice', track_visibility='onchange')
    company_adress = fields.Char(" ", compute='_compute_company_adress')
    state = fields.Selection([
        ('3_cancel', 'Annulé'),
        ('0_draft', 'Brouillon'),
        ('0_to_validate', "À valider"),
        ('1_done', 'Validé'),
        ('2_send', 'Envoyé'),
        ('5_unload', 'Déchargé'),

    ], string="Status", default='0_draft', tracking=True)
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Pièces jointes')
    attachment_name = fields.Char('Attachment Name', related='attachment_ids.name', readonly=False)
    abr_company = fields.Char(string="abreviation et date", default=write_ref)
    new_ref = fields.Char(readonly=True)
    person_send = fields.Char(string="expediteur du courrier", default=person_name)



    def action_to_validate(self):
        if not self.project_id:
            raise UserError(_("Avant de poursuivre, vous devez renseigner le champ projet."))
        for rec in self:
            rec.state = '0_to_validate'
            print("Le a traiter", rec)
            users = self.env['res.users'].search([])

            for u in users:
                groups = u.groups_id.get_xml_id()
                if 'document.securite_directeur' in [group for group in groups.values()]:
                    print("Le if")
                    activity_id = self.env['mail.activity'].create({
                        'summary': "Sortant à valider",
                        'activity_type_id': 4,
                        'res_model_id': self.env['ir.model']._get_id('document.response'),
                        'res_id': self.id,
                        'user_id': u.id
                    })

    def action_draft(self):
        for rec in self:
            rec.state = '0_draft'

    def action_done(self):

        user_writer = self.env.user.name
        name = str(user_writer).split(' ')
        abrv = ""
        for i in name:
            abr = i[0].capitalize()
            abrv += abr
        ref_user = f"{abrv}/MJ"
        x = datetime.now()
        date = x.strftime("%d/%m/%Y")
        abr = self.env.company.abbreviation
        # abr_company = f"{date}/{abr}"
        abr_company = self.abr_company
        sequence = self.reference
        ref = f"{abr_company}/{sequence}/{ref_user}"

        self.new_ref = ref

        for rec in self:
            rec.state = '1_done'
            # Suppression de l'activite de l'administrateur et creation d'une activite pour le profil secretaire
            activity_id = self.env['mail.activity'].search([('res_id', '=', rec.id)])
            print("activity", activity_id)
            if activity_id:
                activity_id.unlink()
                print("activite supprimé")

            users = self.env['res.users'].search([])
            for u in users:
                groups = u.groups_id.get_xml_id()
                print("LEs groups", groups)
                if 'document.securite_secretaire' in [group for group in
                                                      groups.values()] and not 'document.securite_directeur' in [group
                                                                                                                 for
                                                                                                                 group
                                                                                                                 in
                                                                                                                 groups.values()]:
                    activity_id = self.env['mail.activity'].create({
                        'summary': "Sortant à valider",
                        'activity_type_id': 4,
                        'res_model_id': self.env['ir.model']._get_id('document.response'),
                        'res_id': self.id,
                        'user_id': u.id
                    })

    def action_cancel(self):
        for rec in self:
            rec.state = '3_cancel'

    def action_send(self):
        for rec in self:
            # regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            # if rec.email:
            #     if not re.fullmatch(regex, rec.email):
            #         raise ValidationError('Veuillez entrer une adresse E-mail correcte !')
            # if not rec.email:
            #     raise ValidationError("Veuillez renseigner le champs 'Vers' s'il vous plaît !!!")
            # if not rec.subject:
            #     raise ValidationError("Veuillez renseigner le champs 'Objet' s'il vous plaît !!!")
            # if rec.document_id:
            #     rec.document_id.state = '2_send'
            rec.state = '2_send'
            # Suppression de l'activité
            activity_id = self.env['mail.activity'].search([('res_id', '=', rec.id)])
            print("activity", activity_id)
            if activity_id:
                activity_id.unlink()
                print("activite supprimé 2")

        # self.ensure_one()
        # ir_model_data = self.env['ir.model.data']
        # try:
        #     template_id = ir_model_data._xmlid_lookup('document.document_email_template')[2]
        # except ValueError:
        #     template_id = False
        #
        # try:
        #     compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        # except ValueError:
        #     compose_form_id = False
        # ctx = dict(self.env.context or {})
        # ctx.update({
        #     'default_model': 'document.response',
        #     'active_model': 'document.response',
        #     'active_id': self.ids[0],
        #     'default_res_id': self.ids[0],
        #     'default_use_template': bool(template_id),
        #     'default_template_id': template_id,
        #     'default_composition_mode': 'comment',
        #     'custom_layout': "mail.mail_notification_paynow",
        #     'force_email': True,
        #     'mark_rfq_as_sent': True,
        # })
        #
        # lang = self.env.context.get('lang')
        # if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
        #     template = self.env['mail.template'].browse(ctx['default_template_id'])
        #     if template and template.lang:
        #         lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]
        #
        # self = self.with_context(lang=lang)
        # ctx['model_description'] = _('Courrier')
        #
        # return {
        #     'name': _('Compose Email'),
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(compose_form_id, 'form')],
        #     'view_id': compose_form_id,
        #     'target': 'new',
        #     'context': ctx,
        # }

    def action_unload(self):
        for s in self:
            s.state = '5_unload'

    def action_return_document(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "document.document",
            "domain": [('id', '=', self.document_id.id)],
            "name": "Document",
            'view_mode': 'form,kanban,tree',
            'res_id': self.document_id.id
        }
        return result

    @api.model
    def create(self, vals):
        # génération de numéro de référence

        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('response.reference') or _('New')
        res = super(Response, self).create(vals)
        return res

    def preview_response(self):
        # self.ensure_one()
        print("Here")
        # print("Ici", http.request.render('document.preview_response'))
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': "/document/response/preview_response/" + self.reference,
        }

    def write(self, vals):

        for s in self:
            print('write')
            # if vals.get('partner_id') or vals.get('company_id') or vals.get('body'):
            #     historical = self.env['response.historical'].create({
            #         'response_id': s.id,
            #         'partner_id': s.partner_id.id,
            #         'company_id': s.company_id.id,
            #         'body': s.body
            #     })
            # print("Historique cree", historical)
            # action = self.env
            if 'state' in vals:
                # print("State est dans values ow", s.state)
                if vals.get('state') in ['1_done']:
                    if not s.user_has_groups('document.securite_directeur'):
                        raise UserError("Désolé, vous n'êtes habilité à poser cette action. S'il s'agit d'une erreur,"
                                        " Veuillez contacter l'administrateur")
            if vals.get('body'):
                s.message_post(body="Corps du sortant modifié")
            if vals.get('department_ids'):
                print("DepAR", vals.get('department_ids'))
                department_ids = self.env['hr.department'].search([('id', 'in', vals.get('department_ids')[0][2])])
                names = [department_id.name for department_id in department_ids]
                s.message_post(body=f"Départements : {[department_id.name for department_id in s.department_ids]} -> "
                                    f"{[name for name in names]}")
        res = super(Response, self).write(vals)

        return res

    def _response_action_server(self):
        action = {
            'name': 'Sortants',
            'type': 'ir.actions.act_window',
            'res_model': 'document.response',
            'view_mode': 'kanban,tree,form',
            'context': {'search_default_group_2': 1},
            'help': """
                    <p class="o_view_nocontent_smiling_face">
                        Vous n'avez aucun courrier sortant à traiter !
                    </p>
                    """
        }

        verif = 0
        groups = self.env.user.groups_id.get_xml_id()

        for val in groups.values():
            if val == 'document.securite_secretaire' or val == 'document.securite_directeur':
                verif = 1
                break

        # if self.user_has_groups('document.securite_secretaire'):
        if not verif:
            # L'employe lié à l'utilisateur connecté
            employee_id = self.env['hr.employee'].sudo().search([
                ('user_id', '=', self.env.user.id)]).filtered(
                lambda self: self.user_id.company_id.id == self.env.company.id
            )

            responses = self.env['document.response'].search([]).filtered(
                lambda self: employee_id.department_id.id in [
                    department_id.id for department_id in self.department_ids])
            action['domain'] = ['|',
                                ('id', 'in', [doc.id for doc in responses]),
                                ('create_uid', '=', self.env.user.id)
                                ]
            print("Reponses", responses)
        return action

    @api.onchange('company_id_selection')
    def _onchange_company_id_selection(self):
        print("Changing self.company_id")
        self.company_id = self.env['res.company'].sudo().search([('id', '=', int(self.company_id_selection))])
        print("Changing2", self.company_id)
