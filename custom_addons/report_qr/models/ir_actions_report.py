import io

import qrcode
from qrcode.image import pil, svg
from qrcode.image.pil import PilImage, Image, ImageDraw

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
    def qr_generate(self, value, box_size=30, border=5, factory="png", **kwargs):
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

            # 2. Lấy kích thước và vẽ viền bo góc bằng Pillow
            width, height = img.size
            draw = ImageDraw.Draw(img)

            # Thiết lập khoảng cách từ viền khung đến mép ngoài của ảnh (Pixel)
            # Bạn có thể tinh chỉnh số này để viền sát hơn hoặc rộng hơn
            padding = 25

            # Tọa độ góc trên bên trái (x0, y0) và góc dưới bên phải (x1, y1) của khung viền
            x0, y0 = padding, padding
            x1, y1 = width - padding, height - padding

            # Vẽ đường viền hình chữ nhật bo góc (Rounded Rectangle)
            # - radius: độ bo tròn của góc
            # - width: độ dày của đường viền thanh mảnh
            draw.rounded_rectangle(
                [x0, y0, x1, y1],
                radius=45,
                outline=fill_color,
                width=15
            )

            arr = io.BytesIO()
            img.save(arr)
            return arr.getvalue()
        except Exception as e:
            raise ValueError("Cannot convert into barcode.") from e
