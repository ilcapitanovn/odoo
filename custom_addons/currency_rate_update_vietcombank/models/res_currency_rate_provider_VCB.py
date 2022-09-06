import logging
import urllib.request
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
from datetime import datetime, time
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class ResCurrencyRateProviderECB(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("VCB", "Vietcombank")],
        ondelete={"VCB": "set default"},
        default="VCB",
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "VCB":
            return super()._get_supported_currencies()

        # List of currencies obrained from:
        # https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=68
        return [
            "AUD",
            "CAD",
            "CHF",
            "CNY",
            "DKK",
            "EUR",
            "GBP",
            "HKD",
            "INR",
            "JPY",
            "KRW",
            "KWD",
            "MYR",
            "NOK",
            "RUB",
            "SAR",
            "SEK",
            "SGD",
            "THB",
            "USD",
        ]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "VCB":
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        lst_currencies = self._get_supported_currencies()
        invert_calculation = False
        if base_currency != "VND":
            invert_calculation = True
            if base_currency not in currencies:
                currencies.append(base_currency)

        # Depending on the date range, different URLs are used
        url = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=68"
        user_agent = 'Mozilla/5.0'
        headers = {'User-Agent': user_agent}
        request = urllib.request.Request(url=url, headers=headers)

        #response = urllib.request.urlopen(url).read()
        response = urllib.request.urlopen(request).read()
        root = ET.fromstring(response)
        content = {date_to: {}}
        for child in root:
            CurrencyCode = dict(child.attrib).get("CurrencyCode")
            if CurrencyCode not in lst_currencies or CurrencyCode not in currencies:
                continue
            rate = dict(child.attrib).get("Transfer")
            content[date_to].update({CurrencyCode: rate.replace(",", "")})

        if invert_calculation:
            for k in content.keys():
                base_rate = float(content[k][base_currency])
                for currency in content[k].keys():
                    content[k][currency] = str(float(content[k][currency]) / base_rate)
                # content[k]["VND"] = str(1.0 / base_rate)
                content[k]["VND"] = str(base_rate)
        return content

    @api.model
    def scheduled_update_custom(self, service="VCB", date_from=fields.Date.today(), date_to=fields.Date.today()):
        _logger.info("Scheduled currency rates update...")

        # providers = self.search(
        #     [
        #         ("company_id.currency_rates_autoupdate", "=", True),
        #         ("active", "=", True),
        #         ("next_run", "<=", fields.Date.today()),
        #     ]
        # )

        providers = self.env['res.currency.rate.provider'].search(
            [
                ("company_id.currency_rates_autoupdate", "=", True),
                ("active", "=", True),
                ("service", "=", service)
            ], limit=1
        )

        if providers:
            _logger.info(
                "Scheduled currency rates update of: %s"
                % ", ".join(providers.mapped("name"))
            )
            for provider in providers.with_context(**{"scheduled": True}):
                # date_from = (
                #     (provider.last_successful_run + relativedelta(days=1))
                #     if provider.last_successful_run
                #     else (provider.next_run - provider._get_next_run_period())
                # )
                # date_to = provider.next_run
                if (date_to != fields.Date.today()) or (
                        date_to == fields.Date.today()
                        and (
                                not provider._get_close_time()
                                or datetime.now().hour >= provider._get_close_time()
                        )
                ):
                    provider._update(date_from, date_to, newest_only=True)

        _logger.info("Scheduled currency rates update complete.")
