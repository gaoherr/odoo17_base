# -*- coding: utf-8 -*-

from odoo import models, fields, api


class XcModelView(models.Model):
    '''
    Xc model view
    '''
    _name = 'xc_modeler.view'
    _description = 'Xc Model View'
    
    model = fields.Many2one(
        comodel_name='xc_modeler.model', 
        string='Model',  
        ondelete='cascade')
        
    type = fields.Char(string='type')
    xml = fields.Text(string='xml')
    remark = fields.Text(string='remark')
    res_id = fields.Char(string='res_id')
    version = fields.Char(string='version')

    # backup from xc_model_view
    def backup(self, version):
        '''
        backup from xc_model_view_history
        '''
        # copy self data to xc_model_view_history
        self.env['xc_modeler.view_history'].create({
            'model': self.model.id,
            'type': self.type,
            'xml': self.xml,
            'remark': self.remark,
            'res_id': self.res_id,
            'version': self.version,
            'time': fields.Datetime.now(),
            'version': version
        })

    def restore(self, version):
        '''
        restore from xc_model_view_history
        '''
        # unlink all current views
        self.views.unlink()

        # search xc_model_view_history
        view_history = self.env['xc_modeler.view_history'].search([
            ('model', '=', self.model.id),
            ('version', '=', version)
        ])
        # copy self data to xc_model_view_history
        for view_history_item in view_history:
            self.env['xc_modeler.view'].create({
                'model': self.model.id,
                'type': view_history_item.type,
                'xml': view_history_item.xml,
                'remark': view_history_item.remark,
                'res_id': view_history_item.res_id,
                'version': view_history_item.version,
            })

    def get_view_info(self):
        '''
        get view info
        '''
        # read self
        view = self.read([
            'type',
            'xml',
            'remark',
            'res_id',
            'version'
        ])[0]
        return view
