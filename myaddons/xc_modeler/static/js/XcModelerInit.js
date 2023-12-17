(function () {
    'use strict';
    
    // get timestamp
    var timestamp = new Date().getTime();
    
    // load script
    XcloadScript("/xc_modeler/static/js/modeler/ModelerExtend.js?t=" + timestamp).then(function () {
        return XcloadScript("/xc_modeler/static/js/modeler/XcCellExtend.js?t=" + timestamp);
    }).then(function () {
        return XcloadScript("/xc_modeler/static/js/modeler/XcField.js?t=" + timestamp);
    }).then(function () {
        return XcloadScript("/xc_modeler/static/js/modeler/XcTable.js?t=" + timestamp);
    }).then(function () {
        return XcloadScript("/xc_modeler/static/js/modeler/XcModeler.js?t=" + timestamp);
    }).then(function () {
        var editorUiInit = EditorUi.prototype.init;

        EditorUi.prototype.init = function () {
            editorUiInit.apply(this, arguments);
        };

        mxResources.loadDefaultBundle = false;
        var bundle = mxResources.getDefaultBundle(RESOURCE_BASE, mxLanguage) ||
            mxResources.getSpecialBundle(RESOURCE_BASE, mxLanguage);

        var project_id = urlParams['project_id'];
        // Fixes possible asynchronous requests
        mxUtils.getAll([
            bundle, mxBasePath + '/default.xml',
            DATA_PATH + '/table_template.xml?t=' + timestamp,
            DATA_PATH + '/table_row_template.xml?t=' + timestamp,
            DATA_PATH + '/table_header.xml?t=' + timestamp,
            DATA_PATH + '/field_operations.xml?t=' + timestamp,
            '/xc_modeler/get_project_info/' + project_id
        ], function (xhr) {

            // Adds bundle text to resources
            mxResources.parse(xhr[0].getText());

            // Configures the default graph theme
            var themes = new Object();
            themes[Graph.prototype.defaultThemeName] = xhr[1].getDocumentElement();

            // Main, attach to the body
            var editorUi = new EditorUi(new Editor(urlParams['chrome'] == '0', themes));

            var graph = editorUi.editor.graph;
            graph.guidesEnabled = false;
            
            // disable context menu
            editorUi.editor.popupsAllowed = false;

            // disable grid
            graph.setGridEnabled(false);

            // disable selection
            graph.setCellsSelectable(false);

            // disable connection
            graph.setConnectable(false);

            // disable cell edit
            graph.setCellsEditable(false);

            // disable page breaks
            graph.pageBreaksVisible = false;

            var table_template = xhr[2].getText();
            var table_row_template = xhr[3].getText();
            var table_header = xhr[4].getText();
            var field_operations = xhr[5].getText();
            var project_info = JSON.parse(xhr[6].getText());

            // create xc modeler
            var modeler = new XcModeler(editorUi, {
                project_info: project_info,
                templates: {
                    table_template: table_template,
                    table_row_template: table_row_template,
                    table_header: table_header,
                    field_operations: field_operations
                }
            });

            var models = project_info.models;
            if (models.length == 0) {
                // force the graph update
                graph.model.setRoot(graph.getModel().getRoot());
            }

            // save the modeler on the window
            window.xc_modeler = modeler;

        }, function () {
            document.body.innerHTML = '<center style="margin-top:10%;">Error loading resource files. Please check browser console.</center>';
        });
    });
})();