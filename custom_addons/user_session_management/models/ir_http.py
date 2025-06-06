# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith PG (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    """
    Inherits the 'ir.http' abstract model to override its '_authenticate' method
    to update the sid in user.session.login.
    """
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        """
        Overrides odoo.addons.base.models.ir_http._authenticate to update the
        sid in user.session.login.
        """
        res = super()._authenticate(endpoint)
        u_sid = request.session.sid
        usm_session_id = request.session.get('usm_session_id')
        if usm_session_id:
            try:
                current_session = request.env['user.session.login'].sudo().browse(usm_session_id)
                if current_session and current_session.sid != u_sid:    # sid changed after user logged in successful
                    request.env['user.session.login'].browse(usm_session_id).write({
                        'sid': u_sid
                    })
            except Exception as e:
                # Ignore logging if transaction blocked error occurred
                _logger.exception("user_session_management.ir_http._authenticate - Exception: %s" % e)
        return res
