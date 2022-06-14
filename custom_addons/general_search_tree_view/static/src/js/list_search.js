odoo.define('row_no_header_fix_tree_view.list_search', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        events: _.extend({
            'keyup .oe_search_input': '_onKeyUp'
        }, ListRenderer.prototype.events),
        _renderView: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                try {
                    self.$('.o_list_table').addClass('o_list_table_ungrouped');
                    if (self.arch && self.arch.tag == 'tree' && self.arch.attrs) {
                        var isProductPricelist;
                        if (self.el && self.el.baseURI) {
                            isProductPricelist = self.el.baseURI.indexOf('model=product.pricelist');
                        }
                        if (isProductPricelist !== -1) {
                            var hasPricelistRulesAttrs = self.arch.attrs["string"] == "Pricelist Rules";
                            if (hasPricelistRulesAttrs && self.$el.hasClass('o_list_view')) {
                                var search = '<input type="text" class="oe_search_input mt-2 ml-2 pl-3" placeholder="Search...">';
                                self.$el.find('table').addClass('oe_table_search');
                                var $search = $(search).css('border', '1px solid #ccc')
                                .css('width', '99%')
                                .css('height', '28px')
                                self.$el.prepend($search);
                            }
                        }
                    }
                }
                catch (ex) {
                    console.log(ex);
                }
            });
        },
        _onKeyUp: function (event) {
            try {
                var value = $(event.currentTarget).val().toLowerCase();
                var count_row = 0;
                var $el = $(this.$el)
                $(".oe_table_search tr:not(:first)").filter(function() {
                    $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
                    count_row = $(this).text().toLowerCase().indexOf(value) > -1 ? count_row+1 : count_row
                });
            }
            catch (ex) {
                console.log(ex);
            }
        },
    });
});