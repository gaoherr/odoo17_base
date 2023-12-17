
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class XcModelerSyncBaseWizard(models.TransientModel):
    '''
    Sync Base Wizard
    '''
    _name = 'xc_modeler.sync_base_wizard'

    odoo_dir = fields.Char(string='Odoo Dir', required=True)
