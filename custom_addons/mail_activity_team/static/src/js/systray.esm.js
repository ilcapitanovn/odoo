/** @odoo-module **/
import ActivityMenu from "@mail/js/systray/systray_activity_menu";
import {session} from "@web/session";

ActivityMenu.include({
    events: _.extend({}, ActivityMenu.prototype.events, {
        "click .o_filter_button": "_onClickFilterButton",
    }),
    start: function () {
        this._super.apply(this, arguments);
        this.$filter_buttons = this.$(".o_filter_button");
        this.$my_activities = this.$filter_buttons.first();
        this.filter = "my";
        this.user_context = session.user_context;
        this.user_context = _.extend({}, session.user_context, {
            team_activities: false,
        });
    },

    _updateCounter: function () {
        this._super.apply(this, arguments);
        this.$(".o_notification_counter").text(this.activityCounter);
    },

    _onClickFilterButton: function (event) {
        var self = this;
        event.stopPropagation();
        self.$filter_buttons.removeClass("active");
        var $target = $(event.currentTarget);
        $target.addClass("active");
        self.filter = $target.data("filter");

        self.user_context = _.extend({}, session.user_context, {
            team_activities: self.filter === "team",
        });

        self._updateActivityPreview();
    },
    _onActivityFilterClick: function (event) {
        if (this.filter === "my") {
            this._super.apply(this, arguments);
        }
        if (this.filter === "team") {
            var data = _.extend(
                {},
                $(event.currentTarget).data(),
                $(event.target).data()
            );
            var context = {};
            context.team_activities = 1;
            if (data.filter === "my") {
                context.search_default_activities_overdue = 1;
                context.search_default_activities_today = 1;
            } else {
                context["search_default_activities_" + data.filter] = 1;
            }
            this.do_action({
                type: "ir.actions.act_window",
                name: data.model_name,
                res_model: data.res_model,
                views: [
                    [false, "kanban"],
                    [false, "form"],
                ],
                search_view_id: [false],
                domain: [["activity_team_user_ids", "in", session.uid]],
                context: context,
            });
        }
    },
    _getActivityData: function () {
        var self = this;

        return self
            ._rpc({
                model: "res.users",
                method: "systray_get_activities",
                args: [],
                kwargs: {context: self.user_context},
            })
            .then(function (data) {
                self._activities = data;
                self.activityCounter = _.reduce(
                    data,
                    function (total_count, p_data) {
                        return total_count + p_data.total_count || 0;
                    },
                    0
                );
                self.$(".o_notification_counter").text(self.activityCounter);
                self.$el.toggleClass("o_no_notification", !self.activityCounter);
            });
    },
});
