/** @odoo-module **/

import { registry } from "@web/core/registry";


export const PythonService = {

    start() {

        let messager_id = 0;
        let bridge = null;
        let msg_promises = {};

        // 创建 QWebChannel 对象
        if (window.qt) {
            new QWebChannel(qt.webChannelTransport, function (channel) {
            
                // 连接到 Python 中注册的对象
                bridge = channel.objects.bridge;
    
                // 监听从 Python 发送过来的消息
                bridge.messageReceived.connect(function (message) {
                    message = JSON.parse(message);
                    let msg_id = message.id;
                    let status = message.status;
                    if (msg_promises[msg_id]) {
                        if (status == 200) {
                            let result = message.result;
                            msg_promises[msg_id].resolve(result);
                        } else {
                            let error = message.error;
                            msg_promises[msg_id].reject(error);
                        }
                    }
                });
            });
        }

        function call(func_name, args, kwargs) {
            return new Promise((resolve, reject) => {
                messager_id += 1;
                msg_promises[messager_id] = {
                    resolve: resolve,
                    reject: reject,
                };
                let message = {
                    id: messager_id,
                    func_name: func_name,
                    args: args,
                };
                // 在这里你可以使用 bridge 对象调用 Python 中的方法
                bridge.sendMessage(JSON.stringify(message));
            });
        }

        return {
            call: call,
            is_in_shell: () => {
                return window.qt != undefined;
            },
        }
    }
};

registry.category("services").add("python", PythonService);
