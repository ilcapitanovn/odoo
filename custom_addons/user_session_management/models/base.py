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
from ast import literal_eval
from odoo import api, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    """
    Inherited Abstract Model to monitor and log user session activities like
    record creation, modification, deletion, and read.
    """
    _inherit = 'base'

    @api.model
    def _auth_timeout_get_ignored_urls(self):
        """Pluggable method for calculating ignored urls
        Defaults to stored config param
        """
        ignored_urls = self.env["ir.config_parameter"].sudo().get_param('user_session_management.ignored_urls', '')
        return ignored_urls.split(",")
        # TODO: Need to refactor to implement caching for reading config_parameter similar in auth_session_timeout
        # return params._auth_timeout_get_parameter_ignored_urls()

    @api.model
    def create(self, vals_list):
        """
        Overrides the default create method to create a user session activity
        log when a record is created.
        """
        res = super().create(vals_list)
        is_http_context = self._is_http_context()
        if is_http_context:
            models_to_track = self.env['ir.config_parameter'].sudo().get_param(
                'user_session_management.model_ids')
            if models_to_track:
                try:
                    model_ids = self.env['ir.model'].sudo().browse(
                        literal_eval(models_to_track))
                    if model_ids and self._name in model_ids.mapped('model'):
                        name = ''
                        if self._context.get('params') and self._context[
                            'params'].get(
                            'action'):
                            name = self.env['ir.actions.act_window'].sudo().browse(
                                self._context['params']['action']).name or ''
                        if 'name' in vals_list.keys():
                            name = vals_list['name']
                        log_vals = {'name': name,
                                    'model': self._name,
                                    'record': res.id,
                                    'action': 'create',
                                    'login_id': request.session.usm_session_id,
                                    }
                        self.env['user.session.activity'].create(log_vals)
                except Exception as e:
                    # Ignore logging if transaction blocked error occurred
                    _logger.exception("user_session_management.base.create - Exception: %s" % e)
        return res

    def read(self, fields=None, load='_classic_read', log=True):
        """
        Overrides the default read method to create a user session activity
        log when a record is read
        """
        res = super().read(fields, load)
        is_http_context = self._is_http_context()
        if log and is_http_context:
            try:
                ignored_urls = self._auth_timeout_get_ignored_urls()
                if request.httprequest.path not in ignored_urls:
                    models_to_track = self.env['ir.config_parameter'].sudo().get_param(
                        'user_session_management.model_ids')
                    if models_to_track:

                        model_ids = self.env['ir.model'].sudo().browse(
                            literal_eval(models_to_track))
                        if model_ids and self._name in model_ids.mapped('model'):
                            name = ''
                            if self._context.get('params'):
                                if self._context['params'].get('action'):
                                    name = self.env['ir.actions.act_window'].sudo()\
                                               .browse(
                                        self._context['params'][
                                            'action']).name or ''
                            record = False
                            records = ''
                            if len(self) == 1:
                                name = self.name if self._fields.get(
                                    'name') else name
                                record = self.id
                            else:
                                records = self.ids
                            log_vals = {'name': name,
                                        'model': self._name,
                                        'record': record,
                                        'records': records,
                                        'action': 'read',
                                        'login_id': request.session.usm_session_id,
                                        }
                            self.env['user.session.activity'].create(log_vals)
            except Exception as e:
                # Ignore logging if transaction blocked error occurred
                _logger.exception("user_session_management.base.read - Exception: %s" % e)
        return res

    def write(self, vals):
        """
        Overrides the default write method to create a user session activity
        log when a record is modified.
        """
        is_http_context = self._is_http_context()
        if is_http_context:
            models_to_track = self.env['ir.config_parameter'].sudo().get_param(
                'user_session_management.model_ids')
            if models_to_track:
                try:
                    model_ids = self.env['ir.model'].sudo().browse(
                        literal_eval(models_to_track))
                    if model_ids and self._name in model_ids.mapped('model'):
                        res = super().write(vals)
                        name = ''
                        if self._context.get('params') and self._context[
                            'params'].get('action'):
                            name = self.env['ir.actions.act_window'].sudo().browse(
                                self._context['params']['action']).name or ''
                        if 'name' in self._fields.keys():
                            name = self.name
                        log_vals = {'name': name,
                                    'model': self._name,
                                    'record': self.id,
                                    'action': 'modify',
                                    'login_id': request.session.usm_session_id,
                                    }
                        self.env['user.session.activity'].create(log_vals)
                        return res
                except Exception as e:
                    # Ignore logging if transaction blocked error occurred
                    _logger.exception("Error in user_session_management.base.write - Exception: %s" % e)
        return super().write(vals)

    def unlink(self):
        """
        Overrides the default unlink method to create a user session activity
        log when a record is deleted.
        """
        is_http_context = self._is_http_context()
        if is_http_context:
            models_to_track = self.env['ir.config_parameter'].sudo().get_param(
                'user_session_management.model_ids')
            if models_to_track:
                try:
                    model_ids = self.env['ir.model'].sudo().browse(
                        literal_eval(models_to_track))
                    if model_ids and self._name in model_ids.mapped('model'):
                        name = ''
                        if self._context.get('params') and self._context[
                                'params'].get('action'):
                            name = self.env['ir.actions.act_window'].sudo().browse(
                                self._context['params']['action']).name
                        record = False
                        records = ''
                        if len(self) == 1:
                            name = self.name if self._fields.get('name') else name
                            record = self.id
                        else:
                            records = self.ids
                        log_vals = {'name': name,
                                    'model': self._name,
                                    'record': record,
                                    'records': records,
                                    'action': 'delete',
                                    'login_id': request.session.usm_session_id,
                                    }
                        self.env['user.session.activity'].create(log_vals)
                except Exception as e:
                    # Ignore logging if transaction blocked error occurred
                    _logger.exception("user_session_management.base.unlink - Exception: %s" % e)
        return super().unlink()

    @staticmethod
    def _is_http_context():
        # Check if we're in an HTTP request context
        is_http_context = False
        try:
            # Attempt to access something simple from http.request
            if request:
                _ = request.env  # This will fail if unbound
                is_http_context = True
        except RuntimeError as e:
            _logger.info(f"user_session_management.base._is_http_context - No HTTP context available: {e}")
            is_http_context = False

        return is_http_context
