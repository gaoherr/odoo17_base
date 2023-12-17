
# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api


class XcModelerSyncTableWizard(models.TransientModel):
    '''
    Model Project
    '''
    _name = 'xc_modeler.sync_table_wizard'
    _description = 'sync table wizard'

    file_name = fields.Char(string='File Name')
    create_menu = fields.Boolean(string='create menu', default=True)
    root_menus = fields.One2many(
        string='root menu', comodel_name="xc_modeler.root_menus", inverse_name="wizard_id")
    root_menu = fields.Many2one(
        string="Root Menu", comodel_name="xc_modeler.root_menus", domain="[('id', 'in', root_menus)]")
    root_menu_res_id = fields.Char(string='Root Menu Res Id', related='root_menu.res_id')
    sync_model = fields.Boolean(string='sync model', default=True)
    sync_view = fields.Selection(selection=[
        ('sync_when_not_exist', 'sync when not exist'),
        ('force_sync', 'force sync'),
    ], string='sync view', default='sync_when_not_exist')
    
    sync_manifest = fields.Boolean(string='sync manifest', default=True)
    sync_security = fields.Boolean(string='sync security', default=True)
    arrange_files = fields.Boolean(string='arrange files', default=True)
    delete_file_not_exits = fields.Boolean(
        string='delete file not exits', default=True)

    @api.model
    def create_wizard(self, model_id, root_menus):
        """
        create wizard
        """
        model = self.env['xc_modeler.model'].browse(model_id)

        default_menus = []
        for menu in root_menus:
            default_menus.append((0, 0, {
                'name': menu['name'],
                'res_id': menu['res_id'],
            }))
        record = self.create([{
            'file_name': model.file_name,
            'root_menus': default_menus,
        }])
        record.root_menu = record.root_menus[0] if record.root_menu else False
        return record.id
