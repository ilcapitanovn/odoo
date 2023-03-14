odoo.define('freight_mgmt.tree_button', function (require) {
"use strict";
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');
var TreeButton = ListController.extend({
   buttons_template: 'freight_mgmt.buttons',
   events: _.extend({}, ListController.prototype.events, {
       'click .open_booking_list': '_OpenLink',
   }),
   _OpenLink: function () {
       var self = this;
       var url = 'https://docs.google.com/spreadsheets/d/1z-KLNBBYyeAS140XLnC7rmBNa4EFoXox/edit?usp=sharing&ouid=108807027735159553699&rtpof=true&sd=true';
       window.open(url, '_blank');
   }
});
var FreightBookingListView = ListView.extend({
   config: _.extend({}, ListView.prototype.config, {
       Controller: TreeButton,
   }),
});
viewRegistry.add('button_in_tree', FreightBookingListView);
});