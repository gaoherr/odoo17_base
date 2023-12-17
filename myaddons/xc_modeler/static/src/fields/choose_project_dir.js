/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { useService, useOwnedDialogs } from "@web/core/utils/hooks";


export class ChooseProjectDir extends CharField {
    static template = "xc_modeler.choose_project_dir";

    setup() {
        super.setup();
        this.python = useService('python');
    }

    /**
     * choose dir
     * @param {*} event 
     */
    async choose_dir(event) {
        let dir = await this.python.call('choose_dir');
        if (dir) {
            this.props.record.update({ [this.props.name]: dir });
        }
    }
}

export const chooseProjectDir = {
    ...charField,
    component: ChooseProjectDir,
    displayName: _t("Choose Dir"),
};

registry.category("fields").add("choose_project_dir", chooseProjectDir);
