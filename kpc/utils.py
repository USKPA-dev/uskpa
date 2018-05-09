import base64
import io

from django.conf import settings
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, KeepInFrame, Paragraph


def _filterable_params(qd):
    """
       Remove '[]' from querydict keys.
       These are url parameters from multi-value fields
       which have '[]' appended to the name value.
       Django forms need the raw name value.
    """
    qd_out = qd.copy()
    for key, value in qd_out.items():
        if key.endswith('[]'):
            qd_out.setlist(key[:-2], qd_out.pop(key))
    return qd_out


def _to_mdy(dt):
    return dt.strftime("%m/%d/%Y")


class CertificatePreview(object):
    """PDF preview of given Certificate"""
    LINE_1 = 287
    LINE_2 = 250
    LINE_3 = 212
    # Draw Frame boundaries for debugging
    SHOW_BOUNDARY = settings.SHOW_CERT_PDF_ADDRESS_BOUNDARY
    BASE_IMAGE = settings.KPC_BASE
    ADDRESS_FRAME_HEIGHT = 38
    ADDRESS_FRAME_WIDTH = 200

    COORDINATES = {
        'number': [(95, 543), (665, 55)],
        'country_of_origin': (115, 520),
        'aes': (665, 551),
        'date_of_issue': (200, LINE_1),
        'date_of_expiry': (390, LINE_1),
        'shipped_value': (650, LINE_1),
        'exporter': (200, LINE_2),
        'number_of_parcels': (650, LINE_2),
        'consignee': (240, LINE_3),
        'carat_weight': (665, LINE_3),
        'harmonized_code': (350, 175),
        # Drawing in frame, place lower to accomodate border
        'exporter_address': (300, LINE_2-5),
        'consignee_address': (300, LINE_3-5),
    }

    def __init__(self, certificate):
        self.certificate = certificate

    def _get_draw_locations(self, field):
        coords = self.COORDINATES[field]
        if isinstance(coords, list):
            return coords
        else:
            return [coords]

    def _draw_string(self, field, draw_func='drawCentredString', formatter=None):
        """Draw given field at configured location"""
        coordinates = self._get_draw_locations(field)
        drawer = getattr(self.canvas, draw_func)
        for x, y in coordinates:
            output = getattr(self.certificate, field)
            if formatter:
                output = formatter(output)
            drawer(x, y, output)

    def format_country_of_origin(self, value):
        return value.name

    def _paragraph_address(self, field):
        """Convert incoming address into list of Paragraphs"""
        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        value = getattr(self.certificate, field)
        return [Paragraph(line, styleN) for line in value.split('\n')]

    def _draw_address(self, field):
        """
        Draw address fields on certificate
        Using Frames to auto-adjust size/wrapping to fit
        designated area
        """
        x, y = self.COORDINATES[field]
        address_content = self._paragraph_address(field)
        address_frame = Frame(x, y, self.ADDRESS_FRAME_WIDTH,
                              self.ADDRESS_FRAME_HEIGHT,
                              showBoundary=self.SHOW_BOUNDARY,
                              leftPadding=0, bottomPadding=0,
                              rightPadding=0, topPadding=0, )
        inframe = KeepInFrame(content=address_content,
                              maxWidth=self.ADDRESS_FRAME_WIDTH,
                              maxHeight=self.ADDRESS_FRAME_HEIGHT)
        address_frame.addFromList([inframe], self.canvas)

    def make_preview(self):
        kpc_text = io.BytesIO()

        # write KPC text with Reportlab
        self.canvas = canvas.Canvas(kpc_text, pagesize=landscape(letter))

        # draw values
        self._draw_string('number', draw_func='drawString', formatter=str)
        self._draw_string(
            'country_of_origin', formatter=self.format_country_of_origin)
        self._draw_string('aes')
        self._draw_string('date_of_issue', formatter=_to_mdy)
        self._draw_string('date_of_expiry', formatter=_to_mdy)
        self._draw_string('shipped_value', formatter=str)
        self._draw_string('exporter')
        self._draw_string('consignee')
        self._draw_string('number_of_parcels', formatter=str)
        self._draw_string('carat_weight', formatter=str)
        self._draw_string('harmonized_code', formatter=str)

        # draw addresses
        self._draw_address('exporter_address')
        self._draw_address('consignee_address')
        self.canvas.save()

        # render as PDF
        kpc_text.seek(0)
        new_pdf = PdfFileReader(kpc_text)

        # read base PDF
        existing_pdf = PdfFileReader(open(self.BASE_IMAGE, "rb"))
        output = PdfFileWriter()

        # add the "watermark" (which is our new text) on the base kpc pdf
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

        # return base64 string for rendering in template
        pdf_out = io.BytesIO()
        output.write(pdf_out)
        b64_out = base64.b64encode(pdf_out.getvalue()).decode()
        return b64_out
