# -*- coding: utf-8 -*-
{
    'name': "Gestion de courriers",
    'summary': """
        Gestion de courriers
    """,
    'description': """
        Gestion de courriers
    """,
    'author': "Tano Martin, Hydra16",
    'website': "http://www.progistack.com",
    'sequence': 0,
    'application': True,
    'category': 'Project Management',
    'version': '0.1',
    'depends': ['base', 'account_accountant', 'analytic', 'portal', 'contacts', 'hr'],
    'post_init_hook': '_initialise_document_services',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/reference_doc.xml',
        'data/reference_res.xml',
        'data/mail_templates.xml',
        'report/response_report.xml',
        'report/preview_response.xml',
        'report/download_response.xml',
        'views/menu.xml',
        'views/views.xml',
        'views/view_document.xml',
        'views/view_document_type.xml',
        'views/view_response.xml',
        'views/historical_views.xml',
        'views/services_view.xml',
        'views/company_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
