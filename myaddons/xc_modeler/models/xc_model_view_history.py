
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class XcModelViewHistory(models.Model):
    '''
    Model project
    '''
    _inherit = 'xc_modeler.view'
    _name = 'xc_modeler.view_history'
    _description = 'Model View History'
    
    time = fields.Datetime(string='time')
    version = fields.Char(string='version')
