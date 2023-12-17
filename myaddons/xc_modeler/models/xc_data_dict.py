# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DataDict(models.Model):
    '''
    Data Dictionary
    '''
    _name = 'xc_modeler.data_dict'
    _description = 'Data Dictionary'
    
    type = fields.Char(string='type')
    name = fields.Char(string='name')
    remark = fields.Char(string='remark')

    @api.model
    def get_by_type(self, type):
        data_dict = self.serach_read([('type', '=', type)], ['name'])
        return data_dict
