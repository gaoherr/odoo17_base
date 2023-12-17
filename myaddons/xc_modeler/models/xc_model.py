# -*- coding: utf-8 -*-

from math import fabs
from odoo import models, fields, api, exceptions, tools
import logging
import uuid

_logger = logging.getLogger(__name__)


class XcModel(models.Model):
    '''
    Xc model
    '''
    _name = 'xc_modeler.model'
    _description = "Table info"

    name = fields.Char(string="name", default='', index=True)
    model_class_name = fields.Char(string="Model class name", compute="compute_model_class_name")
    model_name = fields.Char(string="Model name", compute="compute_model_name")
    
    description = fields.Text(string="Description", default=False)
    rec_name = fields.Char(string="Rec Name", default=False)
    order = fields.Char(string="Order", default=False)
    parent_name = fields.Char(string="Parent Name", default=False)
    parent_store = fields.Boolean(string="Parent Store", default=False)
    date_name = fields.Char(string="Date Name", default=False)
    fold_name = fields.Char(string="Fold Name", default=False)

    extend_parent = fields.Boolean(string="Extend parent", default=False)
    inherit_models = fields.Text(string="Inherit", default=False, index=True)
    inherits_models = fields.Text(string="Inherits", default=False)

    model_type = fields.Selection(
        [('Model', 'Model'),
         ('TransientModel', 'TransientModel'), 
         ('AbstractModel', 'AbstractModel')], string="Model type", default='Model')

    project = fields.Many2one(comodel_name="xc_modeler.project", string="project", ondelete="cascade")
    project_name = fields.Char(string="project name", related="project.project_name")
    project_path = fields.Char(string="project path", related="project.project_dir")
    file_name = fields.Char(string="File name", help="As some model has no name, so we need a file name to save it", default=False)
    model_fields = fields.One2many(
        string="table fields",
        comodel_name="xc_modeler.field",
        inverse_name="model")
    fields_count = fields.Integer(string="fields_count", compute="compute_fields_count")
    domain = fields.Text(string="list domain")
    views = fields.One2many(comodel_name="xc_modeler.view", inverse_name="model")
    last_backup_views_version = fields.Char(string="last backup views version", default='')
    menu_items = fields.One2many(
        comodel_name="xc_modeler.menu_item", inverse_name="model")
    
    has_menu = fields.Boolean(
        string="Has menu", default=True, help="will generate menu item if there do not exist")
    menu_name = fields.Char(string="Menu name", default=False)

    sql_constrain = fields.Text(string="Sql Constrain")

    pos_x = fields.Integer(string="pos_x", default=0)
    pos_y = fields.Integer(string="pox_y", default=0)
    color = fields.Char(string="color", default='#ffffff')

    remark = fields.Char(string="remark", default='')

    @api.depends("model_fields")
    def compute_fields_count(self):
        '''
        compute fields count
        :return:
        '''
        for record in self:
            record.fields_count = len(record.model_fields)

    @api.onchange('name')
    def onchange_name(self):
        '''
        onchange name
        :return:
        '''
        if self.name and not self.menu_name:
            self.menu_name = self.name.replace('_', ' ')

        if self.name and not self.file_name:
            # replace '  ' to ' '
            self.file_name = self.name.replace('  ', ' ')
            # replace '.' with '_' and ' ' with '_'
            self.file_name = self.name.replace('.', '_').replace(' ', '_')
    
    # get fields info
    def get_fields_info(self, all_inherit_models = []):
        '''
        get fields info
        :return:
        '''
        field_names = []
        fields_info = []
        for field in self.model_fields:
            fields_info.append(field.get_field_info())
            field_names.append(field.name)

        inherit_field_infos = []
        # get inherit fields
        if self.inherit_models and self.inherit_models != '':
            # trim '[' and ']'
            inherit_models = self.inherit_models.strip('[')
            inherit_models = inherit_models.strip(']')
            inherit_models = self.inherit_models.split(',')
            # exclude item in all_inherit_models
            for model in all_inherit_models:
                if model in inherit_models:
                    inherit_models.remove(model)
                    
            # update all_inherit_models
            all_inherit_models.extend(inherit_models)

            # it will get all the inherit fields
            models = self.env['xc_modeler.model'].search([('name', 'in', inherit_models), ('id', '!=', self.id)])
            for model in models:
                tmp_fields = model.get_fields_info()
                 
                # add to inherit fields
                for field in tmp_fields:
                    if field['name'] not in field_names:
                        inherit_field_infos.append(field)
                        field['inherit'] = True
                        field_names.append(field['name'])

        fields_info.extend(inherit_field_infos)

        return fields_info

    def get_view_info(self):
        '''
        get view info
        :return:
        '''
        view_info = []
        for view in self.views:
            view_info.append(view.get_view_info())
        return view_info

    def update_position_info(self, pos_x, pos_y):
        '''
        update ui pos
        :param pos_x:
        :param pos_y:   
        :return:
        '''
        self.pos_x = pos_x
        self.pos_y = pos_y

    # update color  
    def update_color(self, color):
        '''
        update color
        :param color:
        :return:
        '''
        self.color = color

    def del_table(self):
        '''
        :return:
        '''
        self.unlink()

    def compute_model_class_name(self):
        '''
        compute model class name
        :return:
        '''
        for record in self:
            name = record.model_name
            if name and name != '':
                name = name.replace('_', '.')
                name_ar = name.split('.')
                res = ''
                for tmp in name_ar:
                    res += tmp.capitalize()
                record.model_class_name = res
            else:
                # log error
                _logger.error("model name is empty")
                record.model_class_name = ''

    @api.depends("name", "inherit_models")
    def compute_model_name(self):
        '''
        compute table name  
        :return:
        '''
        for record in self:
            name_str = record.name
            if name_str and name_str != '':
                record.model_name = name_str
            elif record.inherit_models and record.inherit_models != '':
                record.model_name = record.inherit_models
            else:
                _logger.error("Model name is empty, and no inherit models! it's not allowed!")

    # check model name exist
    def check_model_name_exist(self, model_name):
        '''
        check model name exist
        :param model_name:
        :return:
        '''
        model_obj = self.env['xc_modeler.model']
        model_ids = model_obj.search([('name', '=', model_name)])
        if len(model_ids) > 0:
            return True
        else:
            return False

    # create model from model info
    def create_model_from_info(self, model_info):
        '''
        create model from model info
        :param model_info:
        :return:
        '''
        model_obj = self.env['xc_modeler.model']
        model_obj.create(model_info)

    # update model from model info
    def update_model(self, model_info):
        '''
        update model from model info
        :param model_info:
        :return:
        '''
        model_fields = model_info.pop('model_fields') if 'model_fields' in model_info else []
        self.update_fields(model_fields)
        if 'views' in model_info:
            views = model_info.pop('views')
            self.update_views(views)
        self.write(model_info)
        
    # get model info
    def get_model_info(self, include_menu_item = True):
        '''
        get model info
        :return:
        '''
        model_info = self.read()[0]

        # deal the file name
        if not self.file_name:
            model_info['file_name'] = self.name.replace('.', '_').replace(' ', '_')

        model_info['model_fields'] = self.get_fields_info() if self.model_fields else []
        # override views
        model_info['views'] = self.get_view_info() if self.views else []
        if include_menu_item:
            records = self.env['xc_modeler.menu_item'].search(
                [('res_model', '=', self.name), ('project', '=', self.project.id)])
            model_info['menu_items'] = records.read() if records else []

        return model_info

    # get model edit form id
    def get_form_res_id(self):
        '''
        get model edit form id
        :return:
        '''
        return self.env.ref('xc_modeler.model_form').id

    # get pop form res id
    @api.model
    def get_pop_form_res_id(self):
        '''
        get model pop form id
        :return:
        '''
        return self.env.ref('xc_modeler.model_pop_form').id 

    @tools.ormcache()
    def get_field_type_cache(self):
        '''
        get field type cache
        :return:
        '''
        records = self.env['xc_modeler.data_dict'].search([('type', '=', 'field_type')])
        # cache by name
        cache = {}
        for record in records:
            cache[record.name] = record.id
        return cache

    # get field type id by name
    def get_field_type_id(self, name):
        '''
        get field type id by name
        :param name:
        :return:
        '''
        return self.get_field_type_cache().get(name)

    # update fields
    def update_fields(self, fields_info):
        '''
        update fields
        :param fields_info:
        :return:
        '''
        # deal field_type 
        for field_info in fields_info:
            field_type = field_info.get('field_type')
            # get feild type id from xc_modeler.data_dict
            field_type = self.get_field_type_id(field_type)
            if not field_type:
                _logger.error("field type %s is not exist!" % field_type)
                field_info['field_type'] = False
                continue
            else:
                field_info['field_type'] = field_type

        # deal comodel_name and inverse_name
        for field_info in fields_info:
            comodel_name = field_info.get('comodel_name')
            if comodel_name:
                field_info['comodel_name_text'] = comodel_name
            if 'comodel_name' in field_info:
                del field_info['comodel_name']

            inverse_name = field_info.get('inverse_name')
            if inverse_name:
                field_info['inverse_name_text'] = inverse_name
            if 'inverse_name' in field_info:
                del field_info['inverse_name']

        # get all xc_model.fields field names
        fields_name_list = self.env['xc_modeler.field']._fields.keys()
        # convert to list
        fields_name_list = list(fields_name_list)
        # apppend selection
        fields_name_list.append('selection')
        # field cache
        field_cache = {field.name: field for field in self.model_fields}
        # format selections
        for field_info in fields_info:
            field_info['changed'] = False
            
            # get keys
            del_keys = []
            for key in field_info.keys():
                if key not in fields_name_list:
                    del_keys.append(key)
            
            # del keys
            for key in del_keys:
                field_info.pop(key)

            field_name = field_info['name']
            selections = [(5, 0, 0)]
            if 'selection' in field_info:
                tmp_selections = field_info['selection'] 
                # check if it is stirng
                if isinstance(tmp_selections, str):
                    try:
                        tmp_selections = eval(tmp_selections)
                    except Exception as e:
                        tmp_selections = []
                elif isinstance(tmp_selections, list) or isinstance(tmp_selections, tuple):
                    for kay_val in tmp_selections:
                        selections.append((0, 0, {
                            'key': kay_val[0],
                            'val': kay_val[1]
                        }))
                field_info['selection'] = selections
            if field_name in field_cache:
                field_cache[field_name].write(field_info)
            else:
                field_obj = self.env['xc_modeler.field']
                vals = {'model': self.id}
                vals.update(field_info)
                try:
                    if not field_info.get('field_type'):
                        continue
                    new_field = field_obj.create(vals)
                    self.model_fields = [(4, new_field.id)]
                    _logger.info("create field %s" % new_field.name)
                except Exception as e:
                    _logger.error("create field %s error: %s" % (field_name, e))

    def backup_views(self):
        '''
        backup views
        :return:
        '''
        # gen a uuid version
        uuid_version = str(uuid.uuid4())
        self.last_backup_views_version = uuid_version

        for view in self.views:
            view.backup(uuid_version)

    def restore_views(self):
        '''
        restore views
        :return:
        '''
        for view in self.views:
            view.restore(self.last_backup_views_version)

    def update_views(self, views_info):
        '''
        update views
        :param views_info:
        :return:
        '''
        self.ensure_one()
        
        # back up first
        self.backup_views()

        if self.name == 'awesome_theme_pro.theme_style':
            print(views_info)

        # get all res_id from views_info
        res_ids = []
        for view_type in views_info:
            views = views_info[view_type]
            for view_info in views:
                res_ids.append(view_info['res_id'])

        # update views
        for view_type in views_info:
            views = views_info[view_type]
            for view_info in views:
                res_id = view_info.pop('res_id')
                # search xc_modeler.view
                view_obj = self.env['xc_modeler.view']
                view = view_obj.search([('res_id', '=', res_id), ('model', '=', self.id)])
                if len(view) > 0:
                    view.write({
                        'type': view_type,
                        'xml': view_info['xml']
                    })
                else:
                    view_obj.create({
                        'res_id': res_id,
                        'model': self.id,
                        'xml': view_info['xml']
                    })

        # delete view not in res_ids
        view_obj = self.env['xc_modeler.view']
        view_ids = view_obj.search([('model', '=', self.id)])
        for view in view_ids:
            if view.res_id not in res_ids:
                view.unlink()

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        """
        check inherit and remove the '[' and ']'
        :param vals:
        :return:
        """
        # check inherit
        if 'inherit' in vals:
            vals['inherit'] = vals['inherit'].lstrip('[').rstrip(']')
        return super(XcModel, self).create(vals)

    def write(self, vals):
        """
        check inherit and remove the '[' and ']'
        :param vals:
        :return:
        """
        # check inherit
        if 'inherit' in vals:
            vals['inherit'] = vals['inherit'].lstrip('[').rstrip(']')
        return super(XcModel, self).write(vals)
