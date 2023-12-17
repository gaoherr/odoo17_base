
# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api


class XcModelerSyncFilesWizard(models.Model):
    '''
    Model Project
    '''
    _name = 'xc_modeler.sync_files_wizard'
    _description = 'false'

    sync_views = fields.Boolean(string='sync views', default=True)
    sync_manifest = fields.Boolean(string='sync manifest', default=True)
    arrange_files = fields.Boolean(string='arrange files', default=True)
