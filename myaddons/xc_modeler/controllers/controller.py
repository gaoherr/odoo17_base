# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
import json
from datetime import datetime, date


class ModelerController(http.Controller):

    def _post_deal_record_data(self, data):
        """
        convert record data to json
        :return:
        """
        if isinstance(data, dict):
            for key, item in data.items():
                if isinstance(item, datetime):
                    data[key] = fields.Datetime.to_string(item)
                if isinstance(item, date):
                    data[key] = fields.Date.to_string(item)
                if isinstance(item, dict):
                    data[key] = self._post_deal_record_data(item)
                if isinstance(item, list):
                    for i in item:
                        if isinstance(i, datetime):
                            data[key] = fields.Datetime.to_string(item)
                        if isinstance(i, date):
                            data[key] = fields.Date.to_string(item)
                        if isinstance(i, dict) or isinstance(i, list):
                            self._post_deal_record_data(i)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, datetime):
                    data[index] = fields.Datetime.to_string(item)
                if isinstance(item, date):
                    data[index] = fields.Date.to_string(item)
                if isinstance(item, dict) or isinstance(item, list):
                    self._post_deal_record_data(item)

    @http.route('/xc_modeler/get_project_info/<int:project_id>', auth='user')
    def get_project_info(self, project_id):
        """
        get project info
        """
        project = request.env['xc_modeler.project'].browse(project_id)
        project_info = project.get_project_info()
        self._post_deal_record_data(project_info)
        return json.dumps(project_info)
