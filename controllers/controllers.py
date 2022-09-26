# -*- coding: utf-8 -*-
from odoo import http


class Response(http.Controller):
    @http.route('/document/response/preview_response/<model("document.response"):response_id>/', website=True)
    def preview_response(self, response_id):
        print("response", response_id)
        return http.request.render('document.preview_response', {'response_id': response_id})

    @http.route('/download/pdf/<model("document.response"):response_id>/', website=True)
    def download_response(self, response_id):
        print("response de downlaod", response_id)
        return http.request.render('document.download_reponse', {
            'response_id': response_id,

        })
    # def index(self, **kw):
    #     return "Hello, world"


#     @http.route('/document/document/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('document.listing', {
#             'root': '/document/document',
#             'objects': http.request.env['document.document'].search([]),
#         })

#     @http.route('/document/document/objects/<model("document.document"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('document.object', {
#             'object': obj
#         })
