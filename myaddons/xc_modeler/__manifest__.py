# -*- coding: utf-8 -*-
{
    "name": "xc_modeler",
    "summary": """
        xc modeler for odoo, it is a rpa tool for odoo developer
    """,
    "description": """
        code generator for odoo, 
        modeler, 
        studio, 
        odoo modeler, 
        odoo modeler, 
        er diagram, 
        code analyser, 
        odoo power designer,
        odoo power code generator
    """,
    "author": "crax",
    "website": "https://www.openerpnext.com",
    "live_test_url": "https://www.openerpnext.com",
    "category": "Apps/studio",
    "price": 00.00,
    "currency": "EUR",

    "depends": ["base", "web"],

    'category': 'App/modeler',
    'version': '17.0.0.3',
    'images': ['static/description/description.gif'],
    'license': 'OPL-1',

    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",

        "views/xc_project.xml",
        "views/xc_field.xml",
        "views/xc_model.xml",
        "views/xc_model_view.xml",
        "views/xc_model_view_history.xml",
        "views/xc_data_dict.xml",
        "views/xc_modeler_selection.xml",
        "views/xc_menu_item.xml",
        "views/xc_menu.xml",

        "data/xc_field_type.xml",
        "views/xc_sync_base_wizard.xml",

        # templates
        'views/templates/controller_init_template.xml',
        'views/templates/controller_template.xml',
        'views/templates/csv_template.xml',
        'views/templates/init_py.xml',
        'views/templates/manifest_template.xml',
        'views/templates/manifest_template_15.xml',
        'views/templates/menu_root.xml',
        'views/templates/model_init.xml',
        'views/templates/model_template.xml',
        'views/templates/view_template.xml',
        'views/templates/view_template_misc.xml',
    ],

    "qweb": [
        "static/xml/*.xml"
    ],

    "assets": {
        "web.assets_backend": [

            "xc_modeler/static/libs/qwebchannel.js",
            "xc_modeler/static/libs/FileSaver.min.js",
            "xc_modeler/static/libs/jszip.min.js",

            "xc_modeler/static/src/fields/choose_project_dir.js",
            "xc_modeler/static/src/fields/choose_project_dir.xml",

            "xc_modeler/static/src/modeler/xc_modeler.js",
            "xc_modeler/static/src/modeler/xc_modeler.xml",
            "xc_modeler/static/src/modeler/xc_modeler.scss",

            # templates
            "xc_modeler/static/xml/*.xml",
            "xc_modeler/static/src/python_service.js",
        ]
    }
}
