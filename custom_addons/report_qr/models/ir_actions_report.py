import io

import qrcode
from qrcode.image import pil, svg
from qrcode.image.pil import PilImage

from odoo import api, models


class ForceRGBImage(PilImage):
    """A custom factory that forces Pillow to use RGB mode instead of monochrome."""
    def new_image(self, **kwargs):
        # Force the underlying Pillow canvas to be 'RGB' mode
        img = super().new_image(**kwargs)
        return img.convert("RGB")


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def qr_generate(self, value, box_size=3, border=5, factory="png", **kwargs):
        factories = {
            "png": pil.PilImage,
            "svg": svg.SvgImage,
            "svg-fragment": svg.SvgFragmentImage,
            "svg-path": svg.SvgPathImage,
        }
        back_color = kwargs.pop("back_color", "white")
        fill_color = kwargs.pop("fill_color", "black")
        try:
            # Defaults to png if the argument is unknown
            image_factory = factories.get(factory, pil.PilImage)
            qr = qrcode.QRCode(
                box_size=box_size, border=border, image_factory=image_factory, **kwargs
            )
            qr.add_data(value)
            qr.make()
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            # img = qr.make_image(
            #     image_factory=ForceRGBImage,
            #     fill_color=(55, 95, 35),  # Dark Green
            #     back_color=(255, 195, 235)  # Light Pink
            # )
            arr = io.BytesIO()
            img.save(arr)
            return arr.getvalue()
        except Exception as e:
            raise ValueError("Cannot convert into barcode.") from e
