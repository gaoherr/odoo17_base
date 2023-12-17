# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re
import os
from .template.manifest_template import manifest
import importlib
from odoo.modules import get_resource_path
import base64


class XcProject(models.Model):
    '''
    Xc project
    '''
    _name = 'xc_modeler.project'
    _description = 'Xc Modeler Project'

    project_name = fields.Char(string="Project Name", required=True, default="New Project")
    name = fields.Char(string="Module Name", required=True, default="New Module")
    project_dir = fields.Char(string="Project Dir", required=True, default="")
    
    base_odoo_project = fields.Boolean(
        string="Base Odoo Project", default=False)

    # there is some difference between versions, like the manifest
    odoo_version = fields.Selection(
        selection=[('10.0', '10.0'),
                   ('11.0', '11.0'),
                   ('12.0', '12.0'),
                   ('13.0', '13.0'),
                   ('14.0', '14.0'),
                   ('15.0', '15.0'),
                   ('16.0', '16.0'),
                   ('17.0', '17.0')],
        default='16.0')
    
    owners = fields.Many2many(
        comodel_name='res.users',
        relation="xc_project_owner_rel",
        column1="src_id",
        column2='dst_id',
        string="Owners")

    summary = fields.Text(string="Summary", default="Xc auto gen project")
    version = fields.Char(string="Version")

    description = fields.Text(
        string="Description",
        default="Xc auto gen project")

    def _get_default_icon(self):
        '''
        get the default small logo
        :return:
        '''
        tmp_path = get_resource_path(
            'xc_modeler', 'static', 'description', 'icon.png')
        return base64.b64encode(open(tmp_path, 'rb') .read())

    icon = fields.Binary(string="Icon", default=_get_default_icon)
    images = fields.Many2many(comodel_name="ir.attachment", string="Images")
    author = fields.Char(string="Author", default="Xc Odoo")
    website = fields.Char(
        string="Website", default="https://www.xcodoo.com")
    live_test_url = fields.Char(string="Live Test Url", default="")
    category = fields.Char(string="Category", default="Xc odoo")
    depends = fields.Text(string="Depends", default="'base', 'web'")
    application = fields.Boolean(string="Application", default=True)

    price = fields.Float(string="Price", default=0)
    license = fields.Char(string="License", default="OPL-1")

    project_models = fields.One2many(
        comodel_name='xc_modeler.model', 
        inverse_name='project', 
        string="Models")

    menu_items = fields.One2many(
        comodel_name='xc_modeler.menu_item', 
        inverse_name='project', 
        string="Menu Items")

    depend_projects = fields.Many2many(
        comodel_name='xc_modeler.project',
        relation="xc_project_depends_rel",
        column1="src_id",
        column2='dst_id',
        compute='_compute_depend_projects',
        string="Depends Project")

    owners = fields.Many2many(
        comodel_name='res.users',
        string="Owners",
        relation="xc_project_owners_rel",
        default=lambda self: [self.env.user.id],
        column1="project_id",
        column2='user_id')

    remark = fields.Char(string="Remark")

    @api.onchange('project_dir')
    def onchange_project_dir(self):
        '''
        onchange project dir
        :return:
        '''
        if self.project_dir:
            index = self.project_dir.rfind('/')
            if index == -1:
                index = self.project_dir.rfind('\\')
            self.project_name = self.project_dir[index + 1:]
            self.name = self.project_dir[index + 1:]

    @api.depends('depends')
    def _compute_depend_projects(self):
        '''
        compute depends project
        :return:
        '''
        for project in self:
            if project.depends:
                project.depend_projects = self.search([('name', 'in', project.depends.split(','))])
            else:
                project.depend_projects = []

    @api.onchange('project_name')
    def onchange_project_name(self):
        '''
        onchange project name
        :return:
        '''
        if self.project_name and not self.name:
            self.name = self.project_name.replace(' ', '_')

    @api.onchange('odoo_version')
    def _onchange_odoo_version(self):
        '''
        onchange odoo version
        :return:
        '''
        if self.odoo_version:
            if not self.version:
                self.version = self.odoo_version + '.0.1'

    def edit_project(self):
        '''
        edit project
        :return:
        '''
        return {
            "type": "ir.actions.client",
            "tag": "xc_modeler",
            "name": self.name,
            "params": {
                "project_id": self.id
            }
        }

    # get all field name of info
    def get_fields_info(self, text):
        """
        get fields info
        :return:
        """
        field_infos = []
        reg_results = re.finditer(
            '\s*([\w]*)[\n\r\s]*=[\n\r\s]*fields\.(.*?)\(.*?\)', text, re.S)
        for result in reg_results:
            field_infos.append({
                "name": result.group(1),
                "type": result.group(2),
                "content": result.group(0),
                "params": result.group(3)
            })
        return field_infos

    # sync project info to database from local files
    def sync_project_info(self):
        '''
        sync project info to database from local files
        :return:
        '''
        # get project infos
        project_infos = self.collect_project_infos(self.project_path)
        # create project dir
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)
        # create files
        for project_info in project_infos:
            # create file
            file_path = project_info['file_path']
            file_dir = os.path.dirname(file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(project_info['class_content'])
        return True

    # build manifest
    def build_manifest(self):
        '''
        build manifest
        :return:
        '''
        template = manifest
        manifest["name"] = self.name
        manifest["project_name"] = self.project_name
        manifest["summary"] = self.summary
        manifest["version"] = self.version
        manifest["author"] = self.author
        manifest["website"] = self.website
        manifest["category"] = self.category
        manifest["depends"] = self.depends
        manifest["version"] = self.version
        manifest["price"] = self.price
        manifest["license"] = self.license
        manifest["depend_projects"] = self.depend_projects
        manifest["remark"] = self.remark
        return template

    # local manifest
    def load_manifest(self):
        '''
        load manifest
        :return:
        '''
        manifest_path = os.path.join(self.project_path, '__manifest__.py')
        if os.path.exists(manifest_path):
            # import manifest
            import_manifest = importlib.import_module(manifest_path)
            self.name = import_manifest.name
            self.summary = import_manifest.summary
            self.version = import_manifest.version
            self.author = import_manifest.author
            self.website = import_manifest.website
            self.category = import_manifest.category
            self.depends = import_manifest.depends
            self.version = import_manifest.version
            self.price = import_manifest.price
            self.license = import_manifest.license
            self.depend_projects = import_manifest.depend_projects
            self.remark = import_manifest.remark
        else:
            # create manifest
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(self.build_manifest())
        return True

    # get models infos
    def get_models_infos(self, include_menu_item=False):
        '''
        get models infos
        :return:
        '''
        models_infos = []
        model_infos = self.project_models.read()
        
        field_ids = []
        for model_info in model_infos:
            # get model fields
            field_ids += model_info['model_fields']
        # read all the fields
        fields_infos = self.env['xc_modeler.field'].browse(field_ids).read()
        fields_info_cache = {field_info['id']: field_info for field_info in fields_infos}

        view_ids = []
        for model_info in model_infos:
            view_ids += model_info["views"]
        # read all the views
        views_infos = self.env['xc_modeler.view'].search_read([('id', 'in', view_ids)], [
            'type',
            'xml',
            'remark',
            'res_id',
            'version'
        ])
        views_info_cache = {view_info['id'] for view_info in views_infos}
        
        # get all the selections
        selection_ids = []
        for field_info in fields_infos:
            if field_info['selection']:
                selection_ids += field_info['selection']

        # read all the selections
        selections_infos = self.env['xc_modeler.selection'].browse(selection_ids).read()
        selections_info_cache = {selection_info['id']: selection_info for selection_info in selections_infos}

        menu_items = self.env['xc_modeler.menu_item'].search([('project', '=', self.id)])
        menu_items_cache = {}
        for menu_item in menu_items:
            menu_items_cache.setdefault(menu_item['name'], []).append(menu_item)

        # model_info
        for model_info in model_infos:
            # deal the fields
            field_ids = model_info['model_fields']
            fields_infos = []
            for field_id in field_ids:
                field_info = fields_info_cache[field_id]
                # deal the selection
                selection_ids = field_info['selection']
                selections = []
                for selection_id  in selection_ids:
                    selection = selections_info_cache[selection_id]
                    selections.append({
                        'key': selection['key'],
                        'val': selection['val']
                    })
                field_info['selection'] = selections
                # if field_info['comodel_name']:
                field_info['comodel_name'] = field_info['comodel_name_text']
                
                if field_info['inverse_name']:
                    field_info['inverse_name'] = field_info['inverse_name'][1]

                if field_info['field_type'][1] not in ['many2one', 'many2many', 'one2many']:
                    field_info['ondelete'] = False

                # deal calss and style
                field_info['class'] = field_info['field_class']
                field_info['style'] = field_info['field_style']
                del field_info['field_class']
                del field_info['field_style']

                field_info['field_type'] = field_info['field_type'][1]
                field_info['model'] = field_info['model'][0]

                if not field_info['string']:
                    field_info['string'] = field_info['name']

                fields_infos.append(field_info)

            model_info['model_fields'] = fields_infos

            # deal the views
            views = []
            # view_ids = model_info['views']
            # for view_id in view_ids:
            #     views.append(views_info_cache[view_id])
            model_info['views'] = views
            if include_menu_item:
                model_info['menu_items'] = menu_items_cache[model_info['name']] or []
            
            models_infos.append(model_info)

        return models_infos

    # get view infos
    def get_views_infos(self):
        '''
        get views infos
        :return:
        '''
        views_infos = []
        for model in self.project_models:
            views_infos.append(model.get_view_info())
        return views_infos

    # get project info
    def get_project_info(self):
        '''
        get project info
        :return:
        '''
        project_info = {
            "project_name": self.project_name,
            "name": self.name,
            "project_dir": self.project_dir,
            "summary": self.summary,
            "version": self.version,
            "author": self.author,
            "website": self.website,
            "category": self.category,
            "depends": self.depends.lstrip('[').rstrip(']'),
            "version": self.version,
            "price": self.price,
            "license": self.license,
            "depend_projects": self.depend_projects.read(),
            "models": self.get_models_infos(include_menu_item=False),
            "views": self.get_views_infos(),
            "menu_items": self.menu_items.read(),
            "website": self.website,
            "live_test_url": self.live_test_url,
            "icon": self.icon.decode('utf-8') if self.icon else False,
            "remark": self.remark
        }

        # deal the model menu items
        model_menu_item_item_cache = {}
        for menu_item in project_info['menu_items']:
            model_id = menu_item['model'][0]
            model_menu_item_item_cache.setdefault(model_id, []).append(menu_item)

        # set the model menu items
        for model in project_info['models']:
            model['menu_items'] = model_menu_item_item_cache.get(model['id'], [])

        # post deal depends
        depends = project_info['depends'] or '[]'
        # check depends start with '['
        if not depends.startswith('['):
            project_info['depends'] = '[' + depends + ']'
        project_info['depends'] = depends

        return project_info

    # update models
    def update_models(self, models_infos):
        '''
        update models
        :return:
        '''
        # get model field names
        model_field_names = self.env['xc_modeler.model']._fields.keys()
        model_field_names = list(model_field_names)
        for model_info in models_infos:
           
            # delete key not in model field names
            del_keys = []
            for key in model_info:
                if key not in model_field_names:
                    del_keys.append(key)
            
            # remove keys
            for key in del_keys:
                del model_info[key]

            # check has a model name
            if model_info.get('name'):
                # as inherit maybe more than one model has the name
                records = self.env['xc_modeler.model'].search(
                    [('name', '=', model_info['name']), ('project', '=', self.id)])
            else:
                # assert inherit_models
                assert model_info.get('inherit_models')
                # search inherit
                records = self.env['xc_modeler.model'].search(
                    [('inherit_models', '=', model_info['inherit_models']), ('project', '=', self.id), ('name', '!=', False)])

            if records:
                for record in records:
                    record.update_model(model_info)
            else:
                vals = {
                    'project': self.id,
                }
                vals.update(model_info)
                model_fields = vals.pop('model_fields')
                if 'views' in vals:
                    views = vals.pop('views')
                else:
                    views = []

                records = self.env['xc_modeler.model'].create(vals)
                records.update_fields(model_fields)
                records.update_views(views)
                
        return True

    # update project info
    def update_project_info(self, project_info):
        '''
        update project info
        :param project_info:
        :return:
        '''
        # update normal info
        self.name = project_info['name']
        self.project_name = project_info.get('project_name', self.project_name)
        self.project_dir = project_info.get('project_dir', self.project_dir)
        self.summary = project_info.get('summary', False)
        self.version = project_info.get('version', False)
        self.author = project_info.get('author', False)
        self.website = project_info.get('website', False)
        self.category = project_info.get('category', False)
        self.depends = project_info.get('depends', False)
        self.version = project_info.get('version', False)
        self.price = project_info.get('price', False)
        self.license = project_info.get('license', False)
        self.remark = project_info.get('remark', False)

        # update models
        self.update_models(project_info.get('models', False))

        # update menu items
        self.update_menu_items(project_info.get('menu_items', []))

        # post deal the field relation batch
        self.post_deal_field_relation()

        return True

    # get addd model form id
    def get_model_form_id(self):
        '''
        get addd model form id
        :return:
        '''
        return self.env.ref('xc_modeler.model_form').id

    # get depends project info
    def get_depend_projects_info(self):
        '''
        get depends project info
        :return:
        '''
        depend_projects_info = []
        for project in self.depend_projects:
            depend_projects_info.append(project.get_project_info())
        return depend_projects_info

    # get project path
    def get_project_path(self):
        '''
        get project path
        :return:
        '''
        return self.project_path

    # get get_depend_projects_info
    def get_depend_projects_info(self):
        '''
        get get_depend_projects_info
        :return:
        '''
        depend_projects_info = []
        for project in self.depend_projects:
            depend_projects_info.append(project.get_project_info())
        return depend_projects_info

    # check is project
    def check_is_project(self, dir):
        '''
        check is project
        :return:
        '''
        project_path = os.path.join(dir, '__manifest__.py')
        if os.path.exists(project_path):
            return True
        else:
            return False

    @api.model
    def update_project_infos(self, project_infos):
        '''
        :param project_infos:
        :return:
        '''
        old_projects = self.search([])
        project_cache = {
            project.project_name: project for project in old_projects}
        for project_info in project_infos:
            project = project_cache.get(project_info['project_name'], False)
            if not project:
                if not project_info.get('name', False):
                    project_info['name'] = project_info['project_name']
                project = self.create({
                    'project_name': project_info['project_name'],
                    'name': project_info['name'],
                    'base_odoo_project': project_info['base_odoo_project'],
                    'project_dir': project_info['project_dir'],
                })
            project.update_project_info(project_info)

    def update_positions(self, position_infos):
        '''
        update positions
        :param positions: 
        :return:
        '''
        # get all table ids
        table_ids = []
        for position_info in position_infos:
            table_ids.append(position_info['id'])
        # get all table
        tables = self.env['xc_modeler.model'].search(
            [('id', 'in', table_ids)])
        # cache the table
        table_cache = {table.id: table for table in tables}
        # update the table
        for position_info in position_infos:
            table = table_cache.get(position_info['id'], False)
            if table:
                table.update_position_info(position_info.get('x', 0), position_info.get('y', 0))
        return True

    def update_menu_items(self, menu_items):
        '''
         update or create menu items
        :param menu_items:
        :return:
        '''
        # get project ids
        project_ids = [self.id]
        for project in self.depend_projects:
            project_ids.append(project.id)

        # get menu item field names
        field_names = self.env['xc_modeler.menu_item']._fields.keys()
        # delete name not in field_names
        for menu_item in menu_items:
            for name in list(menu_item.keys()):
                if name not in field_names:
                    del menu_item[name]
        
        # get project menu items
        old_items = self.env['xc_modeler.menu_item'].search([('id', '=', self.id)])
        # cache the project menu items
        old_item_cache = {
            tmp_item.res_id: tmp_item for tmp_item in old_items}
    
        vals = []
        new_res_ids = []
        for menu_item in menu_items:
            new_res_ids.append(menu_item.get('res_id', False))
            # check exits
            if menu_item['res_id'] in old_item_cache:
                # update
                old_item = old_item_cache[menu_item['res_id']]
                old_item.write(menu_item)
            else:
                vals.append(menu_item)
        menu_model = self.env['xc_modeler.menu_item']
        if len(vals) > 1:
            menu_model.create(vals)
        
        # ids that not in the new_res_ids
        ids_to_delete = []
        for old_item in old_items:
            if old_item.res_id not in new_res_ids:
                ids_to_delete.append(old_item.id)
        if ids_to_delete:
            menu_model.browse(ids_to_delete).unlink()

        # post deal menu item batch
        self.post_deal_menu_item_model()
        return True

    def post_deal_field_relation(self):
        """
        post deal field relation
        """
        # get project ids
        project_ids = [self.id]
        project_ids.extend(self.depend_projects.ids)

        # get all field relation
        fields = self.mapped('project_models.model_fields')
        # get all table
        models = self.env['xc_modeler.model'].search(
            [('project', 'in', project_ids)])
        # cache the table
        model_cache = {model.model_name: model for model in models}
        # update the table
        for field in fields:
            if not field.comodel_name_text:
                continue
            model = model_cache.get(field.comodel_name_text, False)
            if not model:
                continue
            field.comodel_name = model
            if field.inverse_name_text:
                model_fields = model.model_fields
                for model_field in model_fields:
                    if model_field.name == field.inverse_name_text:
                        field.inverse_name = model_field
                        break
        return True

    def post_deal_menu_item_model(self):
        """
        post deal model
        :return:
        """
        # project_ids
        project_ids = [self.id]

        # depend project ids
        depend_project_ids = self.depend_projects.ids
        project_ids.extend(depend_project_ids)

        # get menu items
        menu_items = self.env['xc_modeler.menu_item'].search([('project', 'in', project_ids)])
        model_names = []
        for menu_item in menu_items:
            model_name = menu_item.res_model
            if model_name:
                model_names.append(model_name)

        # get all models
        related_models = self.env['xc_modeler.model'].search(
            [('name', 'in', model_names), ('project', 'in', project_ids)])

        # cache the model
        model_cache = {model.name: model for model in related_models}

        # get all the menu items
        menu_items = self.env['xc_modeler.menu_item'].search(
            [('project', '=', self.id)])

        # set the menu items
        for menu_item in menu_items:
            model_name = menu_item.res_model
            if model_name:
                model = model_cache.get(model_name, False)
                if model:
                    menu_item.model = model.id

    def view_project(self):
        '''
        view project
        :return:
        '''
        self.ensure_one()
        return {
            'name': 'Project',
            'type': 'ir.actions.act_window',
            'res_model': 'xc_modeler.project',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_project_id': self.id}
        }

    def get_project_menu_items(self):
        '''
        get project menu items
        :return:
        '''
        self.ensure_one()
        records = self.env['xc_modeler.menu_item'].search([('project', '=', self.id)])
        return records.read()
    
    def import_project(self):
        """
        import project
        """
        self.ensure_one()
        # get project info
        project_info = self.get_project_info()
        # import project
        self.env['xc_modeler.project'].update_project_infos([project_info])
        return True
    
    @api.model
    def render_template(self, tempalte, context):
        """
        gen model xml
        """
        return self.env['ir.qweb']._render(tempalte, context, escape_mode='xml')
