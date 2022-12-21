# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import report
from odoo import api, SUPERUSER_ID


def auto_install_services(env):
    if not env['document.services'].search([]):
        env['document.services'].create({'service': "Finance"})
        env['document.services'].create({'service': "Juridique"})
        env['document.services'].create({'service': "Direction Generale"})


def auto_update_sequences(env):
    sequences = env['ir.sequence'].search(['|', ('code', '=', 'document.response'), ('code', '=', 'document.document')])
    if sequences:
        print("Sequences", sequences)
        sequences_couriers = sequences.filtered(lambda self: self.prefix == 'DOC-')
        sequences_sortants = sequences.filtered(lambda self: self.prefix == 'RES-')
        for sc in sequences_couriers:
            sc.sudo().write({
                'prefix': "ENT"
            })
        for ss in sequences_sortants:
            ss.sudo().write({
                    'prefix': "SOR"
            })
    else:
        print("Emmanuel, ya pas de sequence tu veux quoi?")

def add_other_to_projects(env):
    other = env['account.analytic.account'].search([('name', '=', 'Autre')])
    if not other:
        env['account.analytic.account'].create({
            'name': 'Autre'
        })

def add_document_type(env):
    other = env['document.type'].search([('name', '=', 'Autre')])
    if not other:
        env['document.type'].create({
            'name': 'Autre'
        })


def _initialise_document_services(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if not env['document.services'].search([]):
        auto_install_services(env)
        auto_update_sequences(env)
        add_other_to_projects(env)
        add_document_type(env)