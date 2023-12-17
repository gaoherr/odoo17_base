# -*- coding: utf-8 -*-

from odoo import models, fields, api


class XcField(models.Model):
    '''
    Xc field
    '''
    _name = 'xc_modeler.field'
    _description = 'table field'
    _order = 'index'

    def get_model_domain(self):
        '''
        get table domain
        :return:
        '''
        project_ids = self.model.project.ids
        project_ids.extend(self.model.project.depend_projects.ids)
        domain = ['|', ('project', 'in', project_ids), ('base_odoo_project', '=', True)]
        return domain

    name = fields.Char(string="Name", required=True)
    string = fields.Char(string="String")
    color = fields.Char(string="Color", default="#ffffff")
    index = fields.Integer(string="Integer", default=0)
    model = fields.Many2one(
        string="Model", comodel_name="xc_modeler.model", ondelete="cascade")
    project_model_ids = fields.One2many(
        string="Project Model",
        comodel_name="xc_modeler.model",
        related="model.project.project_models")

    field_type = fields.Many2one(
        comodel_name="xc_modeler.data_dict",
        string="Field Type",
        domain="[('type', '=', 'field_type')]", required=True)
    field_type_name = fields.Char(
        string="Field Type Name", related="field_type.name")

    # just for x2many field
    comodel_type = fields.Selection(selection=[
        ('project', 'project'),
        ('system', 'system'),
    ], string="Comodel Type", default='project')

    comodel_name_text = fields.Char(string="Comodel Name")
    comodel_name = fields.Many2one(
        string="Comodel",
        comodel_name="xc_modeler.model",
        domain="[('id', 'in', project_model_ids)]",
        ondelete='set null')
    system_comodel = fields.Many2one(
        string="System Comodel",
        comodel_name="ir.model")

    inverse_name_text = fields.Char(string="Inverse Name")
    inverse_name = fields.Many2one(
        string="Inverse",
        comodel_name="xc_modeler.field")

    relation = fields.Char(string="relation", help="relation for many2many")
    column1 = fields.Char(string="column1", help="column1 for many2many")
    column2 = fields.Char(string="column2", help="column2 for many2many")

    widget = fields.Char(string="widget", default="")
    default = fields.Char(string="default")
    domain = fields.Text(string="domain")
    readonly = fields.Boolean(string="readonly")
    invisible = fields.Boolean(string="invisible")
    related = fields.Char(string="related", help="field related")
    required = fields.Boolean(string="Required")
    groups = fields.Text(string="groups")
    store = fields.Boolean(string="store")
    option = fields.Text(string="option", help="option attrs")

    attachment = fields.Boolean(string="attachment")
    ondelete = fields.Char(string="ondelete")

    selection = fields.One2many(
        comodel_name="xc_modeler.selection", 
        inverse_name="owner")
    selection_txt = fields.Text(
        string="Selection", 
        help="selection content when can not deal the selections")
    
    compute = fields.Text(string="Compute")

    field_class = fields.Char(string="Field class")
    field_style = fields.Char(string="Field style")

    changed = fields.Boolean(string="changed", default=False, help="field to show the changed when update")

    help = fields.Char(string="help")
    remark = fields.Text(string="remark")

    @api.onchange('comodel_name')
    def onchange_comodel_name(self):
        '''
        onchange comodel name
        :return:
        '''
        if self.comodel_name:
            self.comodel_name_text = self.comodel_name.model_name

    @api.onchange('field_type')
    def on_change_field_type(self):
        '''
        dynamic gen domain
        :return:
        '''
        table_domain = self.get_model_domain()
        if self.field_type in ['many2one', 'many2many', 'one2many']:
            return {
                'domain': {
                    'comodel_name': table_domain
                }
            }

    @api.onchange('comodel_name')
    def on_change_comodel(self):
        '''
        can only select the related model field
        :return:
        '''
        if self.comodel_name:
            return {
                "domain": {
                    "inverse_name": [('model', "=", self.comodel_name.id)]
                }
            }
        else:
            return {
                "domain": {
                    "inverse_name": [('model', "in", [])]
                }
            }

    @api.onchange('name')
    def onchange_name(self):
        '''
        onchange name
        :return:
        '''
        if self.name and not self.string:
            self.string = self.name

    def get_field_info(self):
        '''
        get field info and get the slection content
        :param field_id:
        :return:
        '''
        res = self.read()[0]

        # deal selections
        selections = self.selection.read(fields=['key', 'val'])
        res['selection'] = selections

        # deal comodel_name
        if self.comodel_name:
            res['comodel_name'] = self.comodel_name.model_name
        # if not have the comodel_name, get the co
        if not self.comodel_name:
            res['comodel_name'] = self.comodel_name_text
        
        if self.inverse_name:
            res['inverse_name'] = self.inverse_name.name

        # deal ondelete if field type not in ['many2one', 'many2many', 'one2many']
        if self.field_type.name not in ['many2one', 'many2many', 'one2many']:
            res['ondelete'] = False

        res['class'] = self.field_class
        res['style'] = self.field_style
        del res['field_class']
        del res['field_style']

        res['field_type'] = self.field_type.name

        if not res['string']:
            res['string'] = self.name

        return res

    def del_field(self):
        '''
        def fileds
        :return:
        '''
        return self.unlink()

    @api.model
    def update_fields_index(self, infos):
        '''
       update index
        :return:
        '''
        for info in infos:
            self.browse(info['id']).write({
                'index': info['index']
            })

    @api.model
    def get_form_res_id(self):
        '''
        get form id
        :param model_id:
        :return:
        '''
        return self.env.ref('xc_modeler.field_form').id

    @api.model
    def get_pop_form_res_id(self):
        '''
        get form id
        :param model_id:
        :return:
        '''
        return self.env.ref('xc_modeler.field_pop_form').id

    def write(self, vals):
        """ 
        rewrite to add the changed field
        """
        # check context has changed
        if self.env.context.get('edit_field', False):
            vals['changed'] = True
        return super(XcField, self).write(vals)

    @api.onchange('system_comodel', 'comodel_name')
    def onchange_system_comodel(self):
        """
        onchange system comodel
        """
        for field in self:
            if field.system_comodel:
                field.comodel_name_text = field.system_comodel.model
            elif field.comodel_name:
                field.comodel_name_text = field.comodel_name.model_name
            else:
                field.comodel_name_text = False

    def get_model_domain(self):
        '''
        get table domain
        :return:
        '''
        project_ids = self.model.project.ids
        project_ids.extend(self.model.project.depend_projects.ids)
        domain = ['|', ('project', 'in', project_ids), ('base_odoo_project', '=', True)]
        return domain
