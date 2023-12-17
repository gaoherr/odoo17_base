# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FieldSelections(models.Model):
    '''
    Field options
    '''
    _name = 'xc_modeler.selection'
    _description = 'Field Selections'

    key = fields.Char(string='key')
    val = fields.Char(string='val')
    owner = fields.Many2one(
        string='owner', 
        comodel_name='xc_modeler.field', 
        ondelete='cascade')
    
    def get_selections(self):
        '''
        get the field selction
        :return:
        '''
        return self.read()