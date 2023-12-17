# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MenuItem(models.Model):
    '''
    Menu item
    '''
    _name = 'xc_modeler.menu_item'
    _description = 'Menu Item'
    
    name = fields.Char(string='Name')
    res_id = fields.Char(string='res_id')
    xml = fields.Text(string='xml')
    parent = fields.Char(string='parent')
    project = fields.Many2one(string='project', comodel_name='xc_modeler.project')
    res_model = fields.Char(string='model')
    model = fields.Many2one(string='model', comodel_name='xc_modeler.model')
    web_icon = fields.Char(string='web_icon')
    icon_data = fields.Binary(string='icon_data')
    path = fields.Char(string='path')
    sequence = fields.Char(string='sequence')
    groups = fields.Char(string='groups')
    is_menu_root = fields.Boolean(string='is_menu_root', compute='_compute_is_menu_root')

    @api.depends('web_icon')
    def _compute_is_menu_root(self):
        for rec in self:
            if not rec.parent:
                rec.is_menu_root = True
            else:
                rec.is_menu_root = False
