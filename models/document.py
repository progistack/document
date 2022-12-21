# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError, UserError


# class HrEmployeePublic(models.Model):
#     _name = "hr.employee"
#     _description = "Employee"
#     _order = 'name'
#     _inherit = ['hr.employee.base', 'mail.thread', 'mail.activity.mixin', 'resource.mixin', 'avatar.mixin']
#     _mail_post_access = 'read'

class Services(models.Model):
    _name = 'document.services'
    _rec_name = 'service'

    service = fields.Char()


class Document(models.Model):
    _name = 'document.document'
    _description = 'Document.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'reference'

    def _set_liste_selection(self):
        company_ids = self.env['res.company'].sudo().search([])
        selection = []
        for company_id in company_ids:
            selection.append((str(company_id.id), company_id.name))

        return selection

    def _get_default_company_id_selection(self):
        print("le default", self.env.company.id)
        return self.env.company.id

    def _get_default_project(self):
        project = self.env['account.analytic.account'].search([('name', '=', 'Autre')])
        return project.id

    def _get_default_document_type(self):
        type_id = self.env['document.type'].search([('name', '=', 'Autre')])
        return type_id.id

    def _domain_employee_sudo(self):
        print("_domain_employee_sudo exec", self)

        employees = self.env['hr.employee'].sudo().search([])
        employee_sudo = self.env['hr.employee.sudo'].search([])

        emp_ids = [emp.id for emp in employees]
        emps_ids = [emps.employee_id for emps in employee_sudo]

        if len(emp_ids) != len(emps_ids):
            for emp_id in emp_ids:
                if not emp_id in emps_ids:
                    try:
                        employee = self.env['hr.employee'].sudo().browse(emp_id)
                        rec = employee_sudo.create({
                                'employee_id': emp_id,
                                'employee_name': employee.name,
                                'employee_email': employee.work_email,
                            })
                        print("Employee créé", rec.employee_name)
                    except:
                        raise ValidationError("Un problème est survenu lors de la récupération des employés. Veuillez contacter l'administrateur si le problème persiste.")

        return []


    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Charger vos fichiers')
    attachment_name = fields.Char('Attachment Name', related='attachment_ids.name', readonly=False)
    type_id = fields.Many2one('document.type', 'Type de courrier', default=_get_default_document_type)
    description = fields.Html('Note', readonly=False)
    company_id = fields.Many2one('res.company', 'Société destinataire', tracking=True)
    company_id_selection = fields.Selection(_set_liste_selection, string="Société destinataire", required=True,
                                            default=_get_default_company_id_selection)
    project_id = fields.Many2one('account.analytic.account', string="Projet", default=_get_default_project)
    partner_id = fields.Many2one('res.partner', string="Émetteur", tracking=True, required=True)
    department_ids = fields.Many2many('hr.department', string="Départements", tracking=True, required=True)
    response_ids = fields.One2many('document.response', 'document_id', string="Sortants")
    response_count = fields.Integer(compute="_compute_response", string='Compteur réponse', copy=False, default=0,
                                    store=True)
    date_of_issue = fields.Date("Date d'émission", index=True, default=fields.Date.today)
    date_of_reception = fields.Datetime("Date de réception", index=True, default=fields.Datetime.now, tracking=True)
    active = fields.Boolean(string="Active", default=True)
    send_mail = fields.Boolean(string="Courrier traité", default=False)
    reference = fields.Char(string='Référence', required=True, copy=False, readonly=True, index=True,
                            default=lambda self: _('New'))
    state = fields.Selection([
        ('0_in_progress', 'En brouillon'),
        ('1_done', 'Réceptionné'),
        ('2_send', 'Courrier traité'),
        ('3_cancel', 'Refusé')
    ], string="Status", default='0_in_progress', tracking=True)
    priority = fields.Selection([
        ('0', 'Non urgent'),
        ('1', 'Normal'),
        ('2', 'Important'),
        ('3', 'Urgent')
    ], string="Priorité", tracking=True)

    service_id = fields.Many2many('document.services')
    restored_historical = fields.Many2one('document.historical', string=(_("Restored Historical")))
    save = fields.Boolean(default=0)

    concerned_employees = fields.Many2many('hr.employee.sudo', domain=_domain_employee_sudo, string="Employées concernés", tracking=True)

    @api.depends("response_ids")
    def _compute_response(self):
        for rec in self:
            rec.response_count = len(rec.response_ids.ids)

    def action_create_response(self):
        print("Creation de reponse", self)
        for rec in self:
            body = f"""
<p>
Madame, Monsieur,
</p>
<p>
...
</p>
<p>
<br><br>
Respectueusement,
</p>
"""
            print("Compamu")
            print(rec.company_id)
            reponse = rec.response_ids.create({
                'email': rec.partner_id.email,
                'department_ids': [department_id.id for department_id in rec.department_ids],
                'project_id': rec.project_id.id,
                'partner_id': rec.partner_id.id,
                'document_id': rec.id,
                'company_id': rec.company_id.id,
                'company_id_selection': str(rec.company_id.id),
                'state': '0_draft',
                'body': body
            })
            print("Reponse cree", reponse)
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Retourne sortant'),
                'res_model': 'document.response',
                'view_mode': 'form',
                'view_id': self.env.ref('document.view_response_form').id,
                # 'domain': [('id', 'in', rec.response_ids.ids)],
                'res_id': reponse.id
            }
            print("Apres action")
            return action

    def action_send_courier(self):
        for rec in self:
            rec.state = '2_send'
            rec.send_mail = True

    def action_in_progress(self):
        for rec in self:
            rec.state = '0_in_progress'

    def action_done(self):
        for rec in self:
            if not rec.partner_id:
                raise ValidationError("Veuillez sélectionner un Émetteur s'il vous plaît !")
            if not rec.project_id:
                raise ValidationError("Veuillez sélectionner un Projet s'il vous plaît !")

            # Reccuperation des pieces jointes
            new_attachments = []
            for attachment in rec.attachment_ids:
                new_attachments.append(attachment.id)
            new_attachments.reverse()
            cmd = [Command.set(new_attachments)]

            try:

                for emp in rec.concerned_employees:
                    print("ma boucle", emp.employee_name)
                    if emp.employee_email:
                        print("Dans le if", rec.reference, rec.description, emp.employee_email, cmd)
                        base_values = {
                            'subject': rec.reference,
                            'body_html': "Bonjour,"
                                         f"{rec.description}"
                                         "Signature",
                            'email_to': emp.employee_email,
                            'attachment_ids': cmd
                        }
                        print("avant mail")
                        mail = self.env['mail.mail'].sudo().create(base_values)
                        print("Avant envoi")
                        mail.send()
                        print("Mail envoyee", mail)
                        rec.sudo().message_post(body=f"Mail envoyé à {emp.employee_name}")
                        print("Apres tout", rec)
                    else:
                        raise ValidationError(f"Aucune adresse mail trouvé pour l'employé {emp.employee_name}")
            except:
                raise ValidationError("Un problème est survenu lors de l'envoi de mail.")

            # Envoi de message aux employees des departements selectionnes
            # print("LEs departements", rec.department_ids)
            for department in rec.department_ids:
                employees = self.env['hr.employee'].sudo().search([('department_id', '=', department.id)])
                partner_ids = [employee.user_id.partner_id.id for employee in employees if
                               employee.user_id and employee.user_id.has_group('document.securite_utilisateur')]

                reference = self.reference
                try:
                    mm = self.env['mail.message'].create({
                        'subject': "Réception de courrier entrant",
                        'email_from': self.env.user.partner_id.email,
                        'author_id': self.env.user.partner_id.id,
                        'model': 'document.document',
                        'message_type': 'notification',
                        'subtype_id': 2,
                        'body': f"Un nouveau courrier réceptionné est adressé au departement {department.name} <h1>Message</h2>",
                        'partner_ids': partner_ids,
                        'res_id': rec.id
                    })
                    # print("After mm", mm)
                    for partner_id in partner_ids:
                        # old_messages = self.env['mail.notification'].sudo().search([
                        #     ('res_partner_id', '=', partner_id), ('notification_type', '!=', 'inbox')]).unlink()
                        # print("Begin pt", partner_id)
                        mn = self.env['mail.notification'].create({
                            'mail_message_id': mm.id,
                            'notification_type': 'inbox',
                            'is_read': False,
                            'res_partner_id': partner_id
                        })
                        # print("message envoye", mm, mn)
                except:
                    raise ValidationError("Un problème est survenu lors de l'envoi de la notification.")

            rec.date_of_reception = fields.Datetime.now()
            rec.state = '1_done'

    def action_cancel(self):
        for rec in self:
            rec.state = '3_cancel'

    def action_return_responses(self):
        self.ensure_one()
        print("Attachment_ids", self.attachment_ids)
        result = {
            "type": "ir.actions.act_window",
            "res_model": "document.response",
            "domain": [('document_id', '=', self.id)],
            "context": {"state": '0_draft'},
            "name": "Sortants",
            'view_mode': 'kanban,tree,form',
        }
        if len(self.response_ids) == 1:
            result['view_mode'] = 'form,kanban,tree'
            result['res_id'] = self.response_ids.id
        return result

    @api.model
    def create(self, vals):
        # génération de numéro de référence
        print("Vals", vals)
        print("Attachment_ids", vals['attachment_ids'])
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('document.reference') or _('New')

        # if vals['name'] is False:
        #     vals['name'] = vals['reference']

        res = super(Document, self).create(vals)
        print("dave ", res.save)
        print("Res2", res.attachment_ids)
        res.write({'save': 1})
        print("save ", res.save)
        return res

    def write(self, vals):
        # for s in self:
        # if vals.get('partner_id') or vals.get('company_id') or vals.get('description'):
        #     historicals = self.env['document.historical'].search([('document_id', '=', s.id)])
        #     print("historicals", historicals)
        #     taille= len(self.env['document.historical'].search([('document_id', '=', self.id)]))
        #     historical = self.env['document.historical'].create({
        #         'reference':  f"{s.reference}/HIS/N.{taille+1}",
        #         'document_id': s.id,
        #         'partner_id': s.partner_id.id,
        #         'company_id': s.company_id.id,
        #         'description': s.description,
        #     })
        #     print("Historical et historicals", historical, historicals)
        #     if historicals:
        #         his = historicals[0]
        #         print("dernier element", his)
        #         his.write({'next_historical': historical.id})
        #         historical.write({'previous_historical': his.id})
        #         print("Enre de previous_historical et next_historical",his.next_historical, historical.previous_historical)
        #     else:
        #         print("Pas d'historique")
        # print("Historique cree", historical)
        # print("Vals", vals)
        if vals.get('attachment_ids'):
            if len(vals.get('attachment_ids')[0][2]) < len(self.attachment_ids):
                self.message_post(body="Pièce jointe retirée.")
            elif len(vals.get('attachment_ids')[0][2]) > len(self.attachment_ids):
                self.message_post(body="Pièce jointe ajoutée.")
        res = super(Document, self).write(vals)
        return res

    def action_return_document_historical(self):
        print("action_return_document_historical exec")
        document = self.env['document.document'].browse(self.id)
        if document:
            action = {
                'name': "Historique du courrier ".format(document.reference),
                'type': 'ir.actions.act_window',
                'res_model': 'document.historical',
                'view_mode': 'tree,form',
                # 'views': [(self.env.ref('document.document_historical_tree'), 'tree'),
                #           (self.env.ref('document.document_historical_form'), 'form')],
                'domain': [('document_id', '=', document.id)]
            }

            if not self.user_has_groups('document.securite_directeur'):
                action['domain'].append(('write_uid', '=', self.env.user.id))

            return action

    def _document_action_server(self):

        action = {
            'name': 'Entrants',
            'type': 'ir.actions.act_window',
            'res_model': 'document.document',
            'view_mode': 'kanban,tree,form',
            'context': {'search_default_filter_in_progress_done': 1},
            'help': """
            <p class="o_view_nocontent_smiling_face">
                Créer votre premier courrier !
            </p>
            """
        }

        # Lorsque c'est un utilisateur de courrier qui est connecte, afficher uniquement les couriers de son departement

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

            documents = self.env['document.document'].search([]).filtered(
                lambda self: employee_id.department_id.id in [
                    department_id.id for department_id in self.department_ids])
            action['domain'] = ['|',
                                ('id', 'in', [doc.id for doc in documents]),
                                ('create_uid', '=', self.env.user.id)
                                ]
            print("Doc", documents)
        return action

    @api.onchange('company_id_selection')
    def _onchange_company_id_selection(self):
        print("Changing", self.company_id)
        self.company_id = int(self.company_id_selection)
        print("Changing2", self.company_id)
