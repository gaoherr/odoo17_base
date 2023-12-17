
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class XcModelerRootMenus(models.TransientModel):
    '''
    Modeler Project
    '''
    _name = 'xc_modeler.root_menus'
    _description = 'root menus for sync wizard'

    wizard_id = fields.Many2one(
        string='wizard', comodel_name="xc_modeler.sync_table_wizard", ondelete='cascade')
    name = fields.Char(string='name', required=True)
    res_id = fields.Char(string='res_id', required=True)
