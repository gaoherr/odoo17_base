/** @odoo-module **/

import {
    Component,
    useExternalListener,
    useRef,
    useState,
} from "@odoo/owl";

import { _t } from "@web/core/l10n/translation";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class XcModeler extends Component {

    setup() {

        super.setup(arguments);

        let params = this.props.action.params;
        let project_id = params.project_id;

        this.project_id = project_id;
        this.rootRef = useRef("root");
        this.iframeRef = useRef("iframe");
        this.fakeRef = useRef("fake_ref");
        this.is_in_shell = window.qt != undefined;

        this.state = useState({
            search_value: '',
        });

        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.python = useService("python");
        this.action = useService("action");

        if (!this.project_id) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                res_model: 'xc_modeler.project',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
            }), {
                clear_breadcrumbs: true,
            };
            return;
        }

        this.addDialog = useOwnedDialogs();

        if (this.project_id) {
            this.host_url = "/xc_modeler/static/index.html?t=" + new Date().getTime()
            this.host_url += "&project_id=" + this.project_id;
        } else {
            this.host_url = false;
        }

        useExternalListener(window, "message", this.onMessage.bind(this));
    }

    /**
     * add view infos to models
     * @param {*} project_info 
     */
    async gen_models_sync_infos(project_info) {

        let menu_items = project_info.menu_items || [];
        let root_menu_res_id = this.get_root_menu_res_id(project_info.project_name, menu_items);

        let models = project_info.models;
        for (let i = 0; i < models.length; i++) {
            let model_info = models[i];
            model_info.root_menu_res_id = root_menu_res_id;
            await this.gen_model_sync_info(model_info);
        }
    }

    async sync_to_project() {
        let self = this;

        if (!this.is_in_shell) {
            this.notification.add(
                "You must run this in shell, this function need local operations!", {
                type: "danger",
            });
            return;
        }

        let project_info = await this.orm.call(
            "xc_modeler.project", "get_project_info", [this.project_id]);
        let result = await this.python.call('collect_project_info_api', [project_info]);
        let status = result.status;
        if (status) {
            let errors = result.errors || [];
            if (errors.length > 0) {
                let error_msg = errors.join("\n");
                self.do_notify(error_msg, "warning");
            } else {
                await this.orm.call(
                    "xc_modeler.project", "update_project_info", [this.project_id, result.project_info]);
                this.reload_iframe();
            }
        }
        else {
            let errors = result.errors || [];
            let error_msg = errors.join("\n");
            self.do_notify(error_msg, "warning");
        }
    }

    reload_iframe() {
        this.iFrame.contentWindow.location.reload(true);
    }

    onMessage(ev) {

        let message = ev.data;

        let action = undefined;
        if (message && message.action) {
            action = message.action;
        } else {
            action = message;
        }

        let data = message.data
        switch (action) {

            case 'xc_modeler:update_position_info':
                var table_id = parseInt(data.table_id);
                var position = data.position;
                this.update_position_info(table_id, position);
                break;

            case 'xc_modeler:add_field':
            case 'xc_modeler:create_field':
                var table_id = parseInt(data.table_id);
                this._add_field(table_id);
                break;

            case 'xc_modeler:delete_field':
                var field_info = data.field_info;
                this._delete_field(field_info);
                break;

            case 'xc_modeler:edit_field':
                var field_id = parseInt(data.field_id);
                this._edit_field(field_id);
                break;

            case 'xc_modeler:delete_table':
                var table_id = parseInt(data.table_id);
                this._delete_table(table_id);
                break;

            case 'xc_modeler:edit_table':
                var table_id = parseInt(data.table_id);
                this._edit_table(table_id);
                break;

            case 'xc_modeler:save_table':
                var table_id = parseInt(data.table_id);
                this._save_table(table_id, false);
                break;

            case 'xc_modeler:download_table':
                var table_id = parseInt(data.table_id);
                this._save_table(table_id, true);
                break;

            case 'xc_modeler:export_svg':
                var svg = data.svg;
                this.save_as_svg(svg);
                break;

            case 'xc_modeler:update_positions':
                var position_infos = data.position_infos;
                this.update_positions(position_infos);
                break;

            case 'xc_modeler:modeler_clicked':
                this.fakeRef.el.click();
                break;

            case 'xc_modeler:on_modeler_ready':
                this.hook_mouse_event();
                break;

            default:
                console.log("Unknown message received: " + message);
                break;
        }
    }

    onIframeLoaded(ev) {
        // on iframe loaded
    }

    // hook mouse event
    hook_mouse_event() {
        // bind mouse move event to document
        $(document).on('mousemove', this.on_mouse_move);

        // bind mouse up event to document
        $(document).on('mouseup', this.on_mouse_up);
    }

    auot_layout() {
        this.call_frame_function('autoLayout');
    }

    add_new_model() {
        var self = this;
        this.orm.call(
            "xc_modeler.model", "get_pop_form_res_id", []).then((form_id) => {
                this.addDialog(FormViewDialog, {
                    resModel: 'xc_modeler.model',
                    viewId: form_id,
                    context: {
                        'default_project': self.project_id
                    },
                    title: _t("Add Table"),
                    onRecordSaved: async (record) => {
                        let res_id = record.data.id;
                        let model_info = await self.orm.call(
                            "xc_modeler.model", "get_model_info", [res_id])
                        self.call_frame_function('addModel', model_info);
                    }
                });
            }
            );
    }

    do_notify(message, type = "info") {
        this.notification.add(message, {
            type: type,
        });
    }

    async update_positions(position_infos) {
        this.orm.call(
            "xc_modeler.project", "update_positions", [this.project_id, position_infos])
    }

    /**
     * save as svg 
     * @param {*} svg 
     */
    async save_as_svg(svg) {
        if (!this.is_in_shell) {
            let filename = "xc_modeler_" + this.project_id + ".svg";
            let blob = new Blob([svg], { type: "image/svg+xml" });
            let url = URL.createObjectURL(blob);
            let a = document.createElement("a");
            a.download = filename;
            a.href = url;
            a.click();
            setTimeout(function () {
                URL.revokeObjectURL(url);
            }, 100);
        } else {
            // choose a dir
            let directory = await this.choose_directory();
            let file_path = directory + "/" + "xc_modeler_" + this.project_id + ".svg";
            this.python.call('save_as_svg', [file_path, svg]).then((result) => {
                if (!result.status) {
                    this.do_notify(result.message, "warning");
                } else {
                    // open the folder
                    this.python.call('open_folder', [directory, "xc_modeler_" + this.project_id + ".svg"]);
                }
            });
        }
    }

    /**
     * add field
     * @param {*} model_id
     * */
    async _add_field(model_id) {

        let viewId = await this.orm.call(
            "xc_modeler.field", "get_pop_form_res_id", []);

        // show form view dialog
        this.addDialog(FormViewDialog, {
            resModel: 'xc_modeler.field',
            viewId,
            context: {
                'default_model': model_id,
            },
            title: _t("Add Field"),
            onRecordSaved: async (record) => {
                let res_id = record.data.id;
                let field_info = await this.orm.call(
                    "xc_modeler.field", "get_field_info", [res_id])
                this.call_frame_function('addField', field_info);
            }
        });
    }

    async _edit_field(field_id) {
        let viewId = await this.orm.call(
            "xc_modeler.field", "get_pop_form_res_id", []);
        this.addDialog(FormViewDialog, {
            resModel: 'xc_modeler.field',
            viewId,
            resId: field_id,
            context: {
                'default_field_id': field_id,
            },
            mode: 'edit',
            title: _t("Edit Field"),
            onRecordSaved: async (record) => {
                let res_id = record.data.id;
                let field_info = await this.orm.call(
                    "xc_modeler.field", "get_field_info", [res_id])
                this.call_frame_function('editField', field_info);
            }
        });
    }

    /**
     * delete field
     * @param {*} field_info 
     */
    async _delete_field(field_info) {
        // rewrite the up code, confirm before
        let result = await this.do_confirm("Delete Confirm!", "Do you want to delete this field?")
        if (result) {
            // call rpc
            await this.orm.call(
                "xc_modeler.field", "unlink", [field_info.id]);
            // notify modeler delete field
            this.call_frame_function('deleteField', field_info);
        }
    }

    choose_directory() {
        return this.python.call('choose_dir')
    }

    async _save_table(model_id, download = false) {

        // convert the above code
        let model_info = await this.orm.call(
            "xc_modeler.model", "get_model_info", [model_id, true]);
        let menu_items = await this.orm.call(
            "xc_modeler.project", "get_project_menu_items", [model_info.project[0]]);
        let root_menu_res_id = this.get_root_menu_res_id(
            model_info.project_name, menu_items);

        // udpate the menu res id
        model_info.root_menu_res_id = root_menu_res_id;

        // gen table xml codedownlo
        this.gen_model_sync_info(model_info)

        if (download) {
            // check in shell
            if (this.is_in_shell) {
                // choose a directory
                let directory = await this.choose_directory();
                if (directory) {
                    return this.download_model_files(model_info, directory);
                } else {
                    return {
                        status: false,
                        message: "User cancel download!"
                    }
                }
            } else {
                return this.download_model_files(model_info);
            }
        } else {
            if (!this.is_in_shell) {
                this.do_notify("Please run in shell!", "warning");
                return Promise.reject({
                    status: false,
                    message: "Please run in shell!"
                });
            } else {
                return this.python.call('sync_model', [model_info]).then(() => {
                    this.do_notify("Sync model to local success!", "succes")
                })
            }
        }
    }

    get_root_menu_res_id(project_name, menu_items) {
        let root_menus = menu_items.filter(function (item) {
            // is_root_menu
            return item.is_root_menu;
        });
        root_menus.sort(function (a, b) {
            return a.sequence - b.sequence;
        });
        // check the length
        if (root_menus.length > 0) {
            return root_menus[0].res_id;
        } else {
            // if not have root menu, create one    
            let res_id = project_name + ".root_menu";
            return res_id;
        }
    }

    // conver camel case to underline
    camel_to_underline(str) {
        var reg = /([A-Z])/g;
        var result = str.replace(reg, "_$1").toLowerCase();
        // trim left '_'
        result = result.replace(/^_/, "");
        return result;
    }

    /**
     * download files
     * @param {*} model_info 
     */
    async download_model_files(model_info, directory) {
        let self = this;

        //use promise to rewrite the up code
        return new Promise(async (resolve, reject) => {
            try {
                // py file
                let model_file = await this.gen_model_py(model_info);
                // trim right blank
                if (directory) {
                    var file_path = directory + "/" + model_info.model_class_name + ".py";
                    this.python.call('do_save_file', [file_path, model_file]).then(function (result) {
                        if (!result.status) {
                            // notify save file error
                            this.do_notify(result.message, "wanning")
                        }
                    });
                } else {
                    var blob = new Blob([model_file], { type: "text/plain;charset=utf-8" });
                    saveAs(blob, model_info.model_class_name + ".py");
                }

                // xml file
                var view_xml = this.gen_model_xml(model_info);
                if (directory) {
                    var file_path = directory + "/" + model_info.model_class_name + ".xml";
                    this.python.call('do_save_file', [file_path, view_xml]).then(function (result) {
                        if (!result.status) {
                            // notify save file error
                            self.do_notify(result.message, "warning");
                        }
                    });
                } else {
                    var blob = new Blob([view_xml], { type: "text/plain;charset=utf-8" });
                    saveAs(blob, model_info.model_class_name + ".xml");
                }

                // csv file
                var csv = this.gen_model_csv_file([model_info]);
                // csv = csv.replace(/\n\s*\n/g, "\n");
                if (directory) {
                    var file_path = directory + "/" + model_info.model_class_name + ".csv";
                    this.python.call('do_save_file', [file_path, csv]).then(function (result) {
                        if (!result.status) {
                            // notify save file error
                            self.do_notify(result.message, "warning");
                        }
                    });
                }
                else {
                    var blob = new Blob([csv], { type: "text/plain;charset=utf-8" });
                    saveAs(blob, model_info.model_class_name + ".csv");
                }

                if (directory) {
                    this.python.call('open_folder', [directory, model_info.model_class_name + ".py"]);
                }
            }
            catch (e) {
                // log
                reject({
                    status: false,
                    message: e.message
                });
            }
        });
    }

    // edit table
    async _edit_table(model_id) {
        let viewId = await this.orm.call(
            "xc_modeler.model", "get_pop_form_res_id", []);
        // show form view dialog
        this.addDialog(FormViewDialog, {
            resModel: 'xc_modeler.model',
            resId: model_id,
            viewId,
            context: {
                'default_project': this.project_id,
                'default_model_id': model_id,
            },
            title: _t("Edit Table"),
            onRecordSaved: async (record) => {
                let res_id = record.data.id;
                let model_info = await this.orm.call(
                    "xc_modeler.model", "get_model_info", [res_id])
                this.call_frame_function('updateTable', model_info);
            }
        });
    }

    // delete table
    async _delete_table(table_id) {
        let result = this.do_confirm("Delete Confirm", "Are you sure to delete this table?");
        if (result) {
            await this.orm.call(
                "xc_modeler.model", "unlink", [table_id]);
            this.call_frame_function('deleteTable', table_id);
        }
    }

    // update position info
    async update_position_info(model_id, position) {
        this.orm.call(
            "xc_modeler.model", "update_position_info", [model_id, position.x, position.y], {}, {
            shadow: true,
        })
    }

    export_as_svg() {
        // call frame fuction to export svg
        this.call_frame_function('exportSvg');
    }

    /**
     * load project data
     * @param {*} project_id 
     */
    async load_project_data(project_id) {
        // get project info
        let project_info = await this.orm.call(
            "xc_modeler.project", "get_project_info", [project_id]);
        // call frame function
        try {
            this.call_frame_function('updateProjectInfo', project_info)
        } catch (error) {
            console.log(error);
        }
    }

    get iFrame() {
        return this.iframeRef.el;
    }

    /**
     * call the iframe function
     * @param {} function_name 
     * @param {*} data 
     */
    call_frame_function(function_name, data) {
        if (this.iFrame && this.iFrame.contentWindow && this.iFrame.contentWindow.xc_modeler) {
            this.iFrame.contentWindow.xc_modeler[function_name](data)
        }
    }

    /**
     * loads depend project info
     * */
    async load_depend_project_info(project_id) {
        // rewrtie the up code
        let project_info = await this.orm.call(
            "xc_modeler.project", "get_depend_project_info", [project_id]);
        let depend_projects = project_info.depend_projects;
        // load depend project infos
        let depend_projects_info = await this.orm.call(
            "xc_modeler.project", "get_depend_projects_info", [depend_projects]);
        return depend_projects_info;
    }

    /**
     * export model
     */
    async download_project(event) {

        // rewrite up code
        let project_info = await this.orm.call(
            "xc_modeler.project", "get_project_info", [this.project_id]);

        var zip = new JSZip();

        var view_xmls = []
        var model_names = []

        var project_name = project_info.name;
        var project_path = project_info.project_dir;

        var menu_items = project_info.menu_items || [];
        var root_menu_res_id = this.get_root_menu_res_id(project_name, menu_items);

        var models = project_info.models;
        for (var i = 0; i < models.length; i++) {

            var model_info = models[i];
            model_info.root_menu_res_id = root_menu_res_id;

            var info = await this.gen_model_sync_info(model_info);
            var py_file_info = info.py_file_info;
            var py_file_path = py_file_info.file_path;

            // replace the project path, convert it to relative path
            py_file_path = py_file_path.replace(project_path, project_name);
            zip.file(py_file_path, py_file_info.file_content);

            var xml_file_info = info.xml_file_info;
            var xml_file_path = xml_file_info.file_path;

            // replace the project path
            xml_file_path = xml_file_path.replace(project_path, project_name);
            zip.file(xml_file_path, xml_file_info.file_content);
            model_names.push(model_info.model_class_name);

            var xml_file_info = info.xml_file_info;
            view_xmls.push(model_info.model_class_name + '.xml');
        }

        // root menu
        var root_menu = this.gen_root_menu(project_info);
        view_xmls.unshift("views/root_menu.xml");
        zip.file(project_name + "/views/root_menu.xml", root_menu);

        // manifest
        var manifest = await this.gen_manifest(project_info, view_xmls);
        // replace true with True and false with False
        manifest = manifest.replace(/true/g, "True").replace(/false/g, "False");
        zip.file(project_name + "/__manifest__.py", manifest);

        // init
        var init_file = await this.gen_init_py();
        zip.file(project_name + "/__init__.py", init_file);

        // csv
        var csv = await this.gen_model_csv_file(project_info.models);
        zip.file(project_name + "/security/ir.model.access.csv", csv);

        // model init
        var model_init = await this.gen_model_init(model_names);
        zip.file(project_name + "/models/__init__.py", model_init);

        // constroller
        let controller_init = await this.gen_controller_init();
        let controller = await this.gen_controller(project_info);

        zip.file(project_name + "/controllers/__init__.py", controller_init);
        zip.file(project_name + "/controllers/controllers.py", controller);

        // zip the icon file
        for (var i = 0; i < menu_items.length; i++) {
            var menu_item = menu_items[i];
            var icon_data = menu_item.icon_data;
            if (icon_data) {
                let project_name = project_info.name;
                // split by ,
                let icon_data_arr = icon_data.split(',');
                // continue if len < 2
                if (icon_data_arr.length < 2) {
                    continue;
                }
                let module_name = icon_data_arr[0];
                let file_path = icon_data_arr[1];
                if (module_name != project_name) {
                    continue;
                }
                // get the file name from path
                let file_name = file_path.substring(file_path.lastIndexOf('/') + 1);
                // create zip folder
                let img = zip.folder("images");
                img.file(file_name, icon_data, { base64: true });
            }
        }

        // download the zip file
        zip.generateAsync({ type: "base64" }).then(async (base64) => {
            // check in shell
            if (this.is_in_shell) {
                // choose a dir
                let dir = await this.choose_directory()
                if (dir) {
                    var file_path = dir + "/" + project_name + ".zip";
                    await this.python.call('save_base64_file', [file_path, base64]);
                    await this.python.call('open_folder', [dir, project_name + ".zip"]);
                } else {
                    // notify user canceled
                    this.do_notify("You canceled the operation.", "warning");
                }
            } else {
                // download the zip file
                var a = document.createElement("a");
                a.href = "data:application/zip;base64," + base64;
                a.download = project_name + ".zip";
                a.click();
            }
        }, function (err) {
            this.do_notify('some thing is error while gen zip file', 'warning')
        });
    }

    async gen_manifest(project_info, view_xmls) {
        let template = 'xc_modeler.manifest_template';
        if (project_info.odoo_version == '15.0') {
            template = 'xc_modeler.manifest_template_15';
        }
        let manifest = await this.renderTemplate(template, {
            'view_xmls': view_xmls,
            'project_info': project_info
        });
        manifest = manifest.replace(/\n\s*\n/g, '\n');
        manifest = manifest.replace(/^\s+|\s+$/g, '');
        return manifest;
    }

    sync_to_files() {

        if (!this.is_in_shell) {
            this.notification.add(
                "Please run the server in debug mode!", {
                type: "danger",
            });
            return;
        }

        this.addDialog(FormViewDialog, {
            resModel: 'xc_modeler.sync_files_wizard',
            title: _t("Add Table"),
            onRecordSaved: async (record) => {
                let res_id = record.data.id;
                let project_info = await this.orm.call(
                    "xc_modeler.project", "get_project_info", [res_id])
                await this.gen_models_sync_infos(project_info);

                // gen manifest info
                let manifest = await this.gen_manifest(project_info, []);

                // set the manifest info
                project_info.manifest = manifest;
                // set the sync options
                project_info.sync_options = record.data;

                if (!this.is_in_shell) {
                    this.notification.add(
                        "Please run the server in debug mode!", { type: "danger" });
                } else {
                    // call sync project to local
                    return this.python.call("sync_project", project_info).then(function (result) {
                        // do notify
                        this.notification.add(
                            "Success", "Sync project to local success!", { type: "success", });
                    })
                }
            }
        });
    }

    async gen_root_menu(project_info) {
        let root_menu = await this.renderTemplate('xc_modeler.menu_root_template', {
            'project_name': project_info.name
        });
        root_menu = root_menu.replace(/\n\s*\n/g, '\n');
        return root_menu;
    }

    async gen_model_init(model_names) {
        let model_init = await this.renderTemplate('xc_modeler.model_init_template', {
            'model_names': model_names
        });
        model_init = model_init.replace(/\n\s*\n/g, '\n');
        return model_init;
    }

    async renderTemplate(template, context) {
        let result = await this.orm.call(
            "xc_modeler.project", "render_template", [template, context])
        result = this.unescape(result);
        return result;
    }

    async gen_controller_init() {
        let txt = await this.renderTemplate('xc_modeler.controller_init_template', {});
        txt = txt.replace(/\s*[\n\r]+\s*/g, '');
        return txt;
    }

    async gen_controller(project_info) {
        let project_name = project_info.name;
        // format name
        project_name = this.format_name(project_name);
        // make the first letter uppercase
        project_name = project_name.charAt(0).toUpperCase() + project_name.slice(1);
        let txt = await this.renderTemplate('xc_modeler.controller_template', {
            'project_name': project_name
        });
        txt = txt.replace(/\s*[\n\r]+\s*/g, '');
        return txt;
    }

    format_name(name) {
        return name.replace(/[^a-zA-Z0-9_]/g, '_');
    }

    short_name(project_name, name) {
        // remove the module name
        name = name.replace(project_name + '.', '');
        name = name.replace(/[^a-zA-Z0-9_]/g, '_');
        return this.camel_to_underline(name);
    }

    /**
     * export table fiels
     * @param {*} model_info 
     * @returns 
     */
    async gen_model_sync_info(model_info) {

        var project_path = model_info.project_path;

        // gen field code first
        var model_fields = model_info.model_fields;
        for (var j = 0; j < model_fields.length; j++) {
            var field = model_fields[j];
            field.code = this.gen_field_code(field);
        }

        // gen menu code
        var menu_items = model_info.menu_items || [];
        for (var k = 0; k < menu_items.length; k++) {
            var menu_item = menu_items[k];
            menu_item.code = this.gen_menu_code(menu_item);
        }

        model_info['py_file_info'] = {
            'file_path': project_path + '/models/' + this.short_name(
                model_info.project_name, model_info.model_name) + '.py',
            'file_content': await this.gen_model_py(model_info)
        }

        model_info['xml_file_info'] = {
            'file_path': project_path + '/views/' + this.short_name(
                model_info.project_name, model_info.model_name) + '.xml',
            'file_content': await this.gen_model_xml(model_info)
        }

        // gen mission views
        this.gen_mission_views(model_info);
        return model_info;
    }

    // gen mission views
    async gen_mission_views(model_info) {
        let views = model_info.views;
        let view_types = []
        for (var i = 0; i < views.length; i++) {
            var view = views[i];
            view['modeler_gen'] = false;
            var view_type = view.view_type;
            view_types.push(view_type);
        }
        if (view_types.indexOf('form') != -1) {
            var res_id = this.format_model_name(model_info.model_name) + '_form';
            var form_view = await this.renderTemplate('xc_modeler.form_view_template', {
                'model_info': model_info,
                'formated_model_name': this.format_model_name(model_info)
            });
            views.push({
                'type': 'form',
                'res_id': res_id,
                'remark': 'Auto Gen',
                'xml': form_view,
                'modeler_gen': true
            })
        } else if (view_types.indexOf('tree') != -1) {
            var res_id = this.format_model_name(model_info.model_name) + '_tree';
            var tree_view = await this.renderTemplate('xc_modeler.list_view_template', {
                'model_info': model_info,
                'formated_model_name': this.format_model_name(model_info)
            });
            views.push({
                'type': 'tree',
                'res_id': res_id,
                'remark': 'Auto Gen',
                'xml': tree_view,
                'modeler_gen': true
            })
        } else if (view_types.indexOf('window_action') != -1) {
            var res_id = this.format_model_name(model_info.model_name) + '_act_window';
            var window_action_view = await this.renderTemplate('xc_modeler.window_action_template', {
                'model_info': model_info,
                'formated_model_name': this.format_model_name(model_info)
            });
            views.push({
                'type': 'window_action',
                'res_id': res_id,
                'remark': 'Auto Gen',
                'xml': window_action_view,
                'modeler_gen': true
            })
        }
        model_info['views'] = views;
    }

    async gen_model_csv_file(models) {
        debugger
        var txt = await this.renderTemplate('xc_modeler.csv_template', {
            models: models
        });
        return txt;
    }

    // gen field code
    gen_field_code(field) {
        let code = "";

        // clone field
        field = JSON.parse(JSON.stringify(field));
        if (field.field_type == 'Selection') {
            // deal selections
            var selections = field.selection;
            var selection_items = [];
            for (var i = 0; i < selections.length; i++) {
                var selection = selections[i];
                if (selection.key && selection.val) {
                    var selection_str = "(\"" + selection.key + "\", \"" + selection.val + "\")";
                    selection_items.push(selection_str);
                }
            }
            if (selection_items.length == 0
                && field.selection_txt) {
                field.selection = field.selection_txt;
            } else {
                field.selection = '[' + selection_items.join(', ') + ']';
            }
        }

        // black list
        var black_list = [
            'id',
            'name',
            'create_uid',
            'create_date',
            'write_uid',
            'write_date',
            'model',
            'color',
            'comodel_name_text',
            'inverse_name_text',
            'field_type',
            'field_type_name',
            'display_name',
            'remark',
            '__last_update'];
        var params = []
        for (var key in field) {

            if (black_list.indexOf(key) != -1) {
                continue;
            }

            if (!field[key]) {
                continue;
            }

            if (key == 'selection' && field.field_type != 'Selection' && field.field_type != 'Reference') {
                continue;
            }

            var val = field[key];

            // check if is string
            if (typeof val == 'string') {
                // check if is val startswith '\'' or '\"', special for default
                if (!val.startsWith('\'')
                    && !val.startsWith('\"')
                    && key != 'default'
                    && key != 'selection') {
                    val = "'" + val + "'";
                }
            }

            // check if it is boolean
            if (typeof val == 'boolean') {
                val = val ? 'True' : 'False';
            }
            params.push(key + "=" + val);
        }
        code = "    " + field.name + " = fields." + field.field_type + "(" + params.join(', ') + ")"
        return code;
    }

    // gen field xml
    gen_field_xml(field) {

        // deal attrs
        var attrs = []

        if (field.string) {
            attrs.push('string="' + field.string + '"')
        } else if (field.required) {
            attrs.push('required="1"')
        } else if (field.readonly) {
            attrs.push('readonly="1"')
        } else if (field.invisible) {
            attrs.push('invisible="1"')
        } else if (field.domain) {
            attrs.push('domain="' + field.domain + '"')
        } else if (field.context) {
            attrs.push('context="' + field.context + '"')
        } else if (field.size) {
            attrs.push('size="' + field.size + '"')
        } else if (field.help) {
            attrs.push('help="' + field.help + '"')
        } else if (field.class) {
            attrs.push('class="' + field.class + '"')
        } else if (field.onchange) {
            attrs.push('onchange="' + field.onchange + '"')
        } else if (field.widget) {
            attrs.push('widget="' + field.widget + '"')
        } else if (field.attrs) {
            attrs.push('attrs="' + field.attrs + '"')
        } else if (field.class) {
            attrs.push('class="' + field.class + '"')
        } else if (field.style) {
            attrs.push('style="' + field.style + '"')
        }

        var res = '<field name="' + field.name + '" ' + attrs.join(' ') + '/>'
        return res;
    }

    // unescape
    unescape(str) {
        return str.replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace('&#39;', '\'')
            .replace('&quot;', '"');
    }

    /**
     * gen views
     */
    async gen_model_xml(model_info) {
        let self = this;
        model_info = JSON.parse(JSON.stringify(model_info));

        let model_fields = model_info.model_fields;
        for (let i = 0; i < model_fields.length; i++) {
            let field = model_fields[i];
            field.xml = self.gen_field_xml(field);
        }

        let xml = await this.renderTemplate("xc_modeler.view_template", {
            "model_info": model_info,
            "fields": model_fields,
            "format_name": this.format_name,
            "formated_model_name": this.format_model_name(model_info)
        })
        return xml;
    }

    // format model name, if not start with project name, add project name
    format_model_name(model_info) {
        let name = model_info.model_name;
        if (name.startsWith(model_info.project_name)) {
            name = model_info.project_name + '.' + name;
        }
        return name;
    }

    async gen_model_py(model_info) {
        let result = await this.orm.call(
            "xc_modeler.project", "render_template", ["xc_modeler.model_template", {
                model_info: model_info,
                fields: model_info.model_fields
            }])
        return result;
    }

    async gen_init_py() {
        var txt = await this.renderTemplate('xc_modeler.init_py', {});
        return txt;
    }

    gen_menu_code(menu_item) {
        var code = "<menu_item ";
        if (menu_item.res_id) {
            code += "res_id='" + menu_item.res_id + "' ";
        } else if (menu_item.action) {
            code += "action='" + menu_item.action + "' ";
        } else if (menu_item.web_icon) {
            code += "web_icon='" + menu_item.web_icon + "' ";
        } else if (menu_item.sequence) {
            code += "sequence='" + menu_item.sequence + "' ";
        } else if (menu_item.parent) {
            code += "parent='" + menu_item.parent + "' ";
        } else if (menu_item.groups) {
            code += "groups='" + menu_item.groups + "' ";
        }
    }

    async do_confirm(title, message) {
        return new Promise((resolve, reject) => {
            this.addDialog(ConfirmationDialog, {
                title: title,
                body: message,
                confirmLabel: _t("Ok"),
                cancelLabel: _t("Cancel"),
                confirm: () => {
                    resolve(true);
                },
                cancel: () => {
                    resolve(false);
                }
            });
        })
    }

    /**
     * do search
     * @param {*} event 
     */
    do_search(event) {
        let search_value = this.state.search_value;
        let project_id = this.project_id;
        let models = this.orm.call("xc_modeler.model", "search_model", [project_id, search_value])
        return models;
    }
}

XcModeler.template = "xc_modeler.modeler";
XcModeler.components = {
    Dropdown,
    DropdownItem,
};
registry.category("actions").add("xc_modeler", XcModeler);
