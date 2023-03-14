odoo.define('seenpo_hr_attendance.tree_button', function (require) {
"use strict";
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');
var TreeButton = ListController.extend({
   buttons_template: 'seenpo_hr_attendance.buttons',
   events: _.extend({}, ListController.prototype.events, {
       'click .refresh_attendance_log': '_DoAction',
   }),
   _DoAction: function () {
       var self = this;
       if (self.inProgress == 2) {
        console.log("Action is in progress!!");
        return;
       }
       self.inProgress = 2;
       self._rpc({
            model: 'seenpo.hr.attendance.bio.log',
            method: 'refresh_bio_attendance_log',
            args: [this.getSession().user_id], //Now gives the value of c.

        })
        .then(function(res){
            console.log(res);   //it gives object
            self.inProgress = false;
            self.do_action('reload');
        })
        .catch((err) => {
            console.error(err);
            self.inProgress = false;
        })
        .finally(() => {
            console.log('Request completed');
            self.inProgress = false;
        });
   }
});
var AttendanceRefreshListView = ListView.extend({
   config: _.extend({}, ListView.prototype.config, {
       Controller: TreeButton,
   }),
});
viewRegistry.add('button_refresh_attendance_log', AttendanceRefreshListView);
});