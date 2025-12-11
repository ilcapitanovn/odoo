odoo.define('freight_mgmt.group_label_patch', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');

    const _superRenderGroup = ListRenderer.prototype._renderGroup;

    function getDomRoot(maybeEl) {
        // Case 1: direct DOM element
        if (maybeEl && typeof maybeEl.querySelector === "function") {
            return maybeEl;
        }
        // Case 2: jQuery object
        if (maybeEl && maybeEl instanceof jQuery && maybeEl[0] instanceof Element) {
            return maybeEl[0];
        }
        // Case 3: [ jQueryObject ]
        if (Array.isArray(maybeEl) &&
            maybeEl[0] instanceof jQuery &&
            maybeEl[0][0] instanceof Element) {
            return maybeEl[0][0];
        }
        // Case 4: [ DOM Element ]
        if (Array.isArray(maybeEl) && maybeEl[0] instanceof Element) {
            return maybeEl[0];
        }
        // Case 5: renderer.el
        if (maybeEl && maybeEl.el && maybeEl.el.querySelector) {
            return maybeEl.el;
        }
        return null;
    }

    ListRenderer.prototype._renderGroup = function (group, groupLevel) {
        const el = _superRenderGroup.apply(this, arguments);

        if (group && group.model === 'sale.incentive.analysis.report') {

            // pick DOM root safely
            const root = getDomRoot(el);

            // 1. Define the correct CSS selector
            const selector = ".display_achieve";

            // 2. Select ALL matching elements within the root (e.g., the current view container)
            // We use querySelectorAll because you likely have multiple rows/elements to update.
            const statusElements = root.querySelectorAll(selector);

            // 3. Loop through the NodeList and update the content of each element
            statusElements.forEach(element => {
                // Get the current text content and trim whitespace
                const currentValue = element.textContent.trim();

                if (currentValue === '0') {
                    element.textContent = 'Không Đạt';
                } else if (currentValue === '1') {
                    element.textContent = 'Đạt';
                }
            });
        }

        return el;
    };
});