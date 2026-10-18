// /** @odoo-module **/
// // BusListener.js
// import { registry } from "@web/core/registry";
//
//
// const myService= {
//     dependencies: ['bus_service'],
//     start(_, { bus_service }) {
//         console.log('Add notification');
//         bus_service.addChannel('my-event'); // New channel
//         bus_service.addEventListener('notification', ({ detail: notifications }) => {
//             console.log({ notifications });
//             for (const { payload, type } of notifications) {
//                 if (type==="my-event") {
//                     this.myEventHandler(payload);
//                 }
//             }
//         });
//         bus_service.addEventListener('connect', () => {
//             console.log('Connected');
//         });
//         bus_service.start();
//     },
//     myEventHandler(event) {
//         console.log({ event });
//     }
// };
// registry.category("services").add("myService", myService);


odoo.define('freight_credit_control.page_refresh', function (require) {
"use strict";

var WebClient = require('web.WebClient');
var core = require('web.core');

var bus = require('bus.bus').bus;
    bus.on('broadcast', this, function (message) {
        console.log('Received message:', message);
    });
//
// // WebClient.include({
// //     /**
// //      * @override
// //      */
// //     start: function () {
// //         var self = this;
// //         return this._super.apply(this, arguments).then(function () {
// //             self._initPageRefreshBus();
// //         });
// //     },
// //
// //     /**
// //      * Subscribe to longpolling bus for page refresh notifications
// //      * @private
// //      */
// //     _initPageRefreshBus: function () {
// //         var self = this;
// //
// //         // Ensure call_service for bus is available
// //         if (this.call) {
// //             // Add 'broadcast' channel to the longpolling listener
// //             this.call('bus_service', 'addChannel', 'broadcast');
// //
// //             // Listen for incoming bus notifications
// //             this.call('bus_service', 'onNotification', this, function (notifications) {
// //                 _.each(notifications, function (notification) {
// //                     var channel = notification[0];
// //                     var message = notification[1];
// //
// //                     if (channel === 'broadcast' && message && message.type === 'page_refresh') {
// //                         self._handlePageRefreshNotification(message.payload);
// //                     }
// //                 });
// //             });
// //         }
// //     },
// //
// //     /**
// //      * Execute soft or hard reload depending on current view type
// //      * @private
// //      */
// //     _handlePageRefreshNotification: function (payload) {
// //         if (!payload || !payload.model_name) {
// //             return;
// //         }
// //
// //         var currentUrl = window.location.href;
// //
// //         // Check if user is currently looking at the target model
// //         if (currentUrl.indexOf('model=' + payload.model_name) !== -1) {
// //             console.log("[Page Refresh] Notification received for model:", payload.model_name);
// //
// //             var hash = window.location.hash.slice(1);
// //             var urlParams = new URLSearchParams(hash);
// //
// //             // SPA Reload via Action Manager (No browser F5 flash)
// //             if (urlParams.get('view_type') === 'form') {
// //                 console.log("[Page Refresh] Executing hard reload");
// //                 this.do_action({
// //                     type: 'ir.actions.client',
// //                     tag: 'reload',
// //                 });
// //             } else {
// //                 console.log("[Page Refresh] Executing soft reload for Kanban/List");
// //                 this.do_action({
// //                     type: 'ir.actions.client',
// //                     tag: 'soft_reload',
// //                 });
// //             }
// //         }
// //     }
// // });
//
});