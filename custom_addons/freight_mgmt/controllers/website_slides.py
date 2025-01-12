# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.addons.website_slides.controllers.main import WebsiteSlides


class WebsiteSlidesInherit(WebsiteSlides):

    @http.route('/slides', type='http', auth="user", website=True, sitemap=True)
    def slides_channel_home(self, **kwargs):
        # Call the original method to retain functionality
        return super(WebsiteSlidesInherit, self).slides_channel_home(**kwargs)
