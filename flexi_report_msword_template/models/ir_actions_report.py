# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
import base64
import tempfile
from docxtpl import DocxTemplate
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from PyPDF2 import  PdfFileReader, PdfFileWriter
import requests
import socket
import os
import logging
_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    msword_template_file = fields.Binary('Ms template file', attachment=True)
    msword_template_name = fields.Char('Ms template name')
    is_msword_report = fields.Boolean('Is MS Word report', default=False)
    msword_export_type = fields.Selection([('docx-pdf','PDF'), ('docx-simple','Docx')],
                                          string='Export format', default='docx-simple',
                                          help="docx-pdf: The report will be rendered as pdf "
                                               "docx-raw: The report will rendered as raw docx")

    print_view = fields.Boolean('Print View', default=False)

    def _get_suffix(self):
        return str(self.msword_template_name).split(".")[-1]

    def build_full_url(self, http_base_url, url_path):
        if not http_base_url or not url_path or not isinstance(http_base_url, str) \
                or not isinstance(url_path, str):
            raise UserError(_("Invalid parameters to build http full url"))

        while http_base_url[-1] == "/":
            http_base_url = http_base_url[:-1]

        return http_base_url + url_path

    def convert_docx_to_pdf(self, report_name, source, timeout=15):
        filetmp = tempfile.NamedTemporaryFile(suffix='.docx')
        filetmp.write(source)
        filetmp.seek(0)
        try:
            # Conversion du document .docx en PDF avec Gotenberg
            base_url = str()
            response = requests.post(self.build_full_url(self.env.user.company_id.gotenberg_http_base_url, '/forms/libreoffice/convert'),
                files={'files': (report_name, filetmp.name,
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')},
                data={'pdfa': 'PDF/A-1b'}
            )

            # Gestion des erreurs de conversion
            if response.status_code != 200:
                raise ValidationError(_("Error during report document conversion to PDF using Gotenberg: %s" % response.text))

            # Récupération des données PDF et préparation de la réponse
            return response.content
        except (requests.RequestException, socket.error) as net_err:
            raise ValidationError(_('Unable to contact Gontenberg server: %s' % str(net_err)))
        finally:
            filetmp.close()
            # Suppression du fichier temporaire
            if os.path.exists(filetmp.name):
                os.remove(filetmp.name)

    def merge_and_export_base64_pdfs(self, docx_array):
        pdf_writer = PdfFileWriter()

        for docx in docx_array:
            pdf = self.convert_docx_to_pdf(docx['name'], docx['data'])
            pdf_reader = PdfFileReader(BytesIO(pdf))
            for page in range(len(pdf_reader.pages)):
                pdf_writer.addPage(pdf_reader.pages[page])

        output_pdf_stream = BytesIO()
        pdf_writer.write(output_pdf_stream)
        output_pdf_stream.seek(0)
        pdf = output_pdf_stream.read()
        #merged_pdf_base64 = base64.b64encode(output_pdf_stream.read()).decode('utf-8')
        return pdf

    def _zip_mutil_file_docx(self, files):
        tempfile_zip = tempfile.NamedTemporaryFile(suffix='zip')
        with ZipFile(tempfile_zip, 'w', ZIP_DEFLATED) as zipf:
            for fc in files:
                temp_file = BytesIO(fc['data'])
                doc = Document(temp_file)
                temp_docx_stream = BytesIO()
                doc.save(temp_docx_stream)
                temp_docx_stream.seek(0)
                file_name = fc['name']
                zipf.writestr(f'{file_name}.docx', temp_docx_stream.read())
        with open(tempfile_zip.name, 'rb') as zip_file:
            zip_binary_value = zip_file.read()
        return zip_binary_value

    def _render_docx_tpl(self, report_ref, res_ids=None, data=None):
        if not res_ids:
            raise UserError(_("There is no records to render docx template"))
        if not data:
            data = {}
        if isinstance(res_ids, int):
            res_ids = [res_ids]
        data.setdefault('report_type', 'pdf')
        ########
        # access the report details with sudo() but evaluation context as current user
        report_sudo = self._get_report(report_ref)
        datas = self.env[report_sudo.model].browse(res_ids)
        # datas = self.env[self.model].browse(res_ids)
        file_path = self.create_temp_file_from_data(self.msword_template_file)
        docx_array = list()
        for current_obj in datas:
            docx_rendered = DocxTemplate(file_path)

            context = {'o': current_obj}
            docx_rendered.render(context)
            output = BytesIO()
            docx_rendered.save(output)
            output.seek(0)
            docx_array.append({'name': "%s-%s" % (str(current_obj._name).replace('.','-'), current_obj.id),
                               'data': output.getvalue(),
                               })

        if self.msword_export_type == "docx-simple":
            if len(docx_array) > 1:
                file = self._zip_mutil_file_docx(docx_array)
                return file, 'zip'
            else:
                return docx_array[0], self._get_suffix()
        else:
            if len(docx_array) > 1:
                file = self.merge_and_export_base64_pdfs(docx_array)
                return file, 'pdf'
            else:
                file = self.convert_docx_to_pdf(docx_array[0]['name'], docx_array[0]['data'])
                return file, 'pdf'

    def create_temp_file_from_data(self, file_data):
        """
        Create a temporary file from base64-encoded data.

        :param file_data: Base64-encoded data as a string.
        :return: Path to the temporary file.
        """
        temp_data = base64.b64decode(file_data)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(temp_data)
            temp_file_path = temp_file.name

        return temp_file_path

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if not self.is_msword_report:
            result = super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids, data)
        else:
            result = self._render_docx_tpl(report_ref, res_ids, data)

        return result

    def _iter_block_items(self, parent):
        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("something's not right")
        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    def _match_and_replace(self, block, record, fields):
        matched_field = list(filter(lambda field: field == block.text.strip(), fields))
        block_text_array = []
        if len(matched_field) == 0:
            block_text_array = block.text.strip().split('.')
            block_text = ''
            i = 0
            for text in block_text_array:
                if i > 0:
                    if i == 1:
                        block_text += text
                    else:
                        block_text += '.' + text
                i += 1
            matched_field = list(filter(lambda field: field == block_text, fields))
        if len(block_text_array) <= 1:
            if matched_field and not hasattr(record, matched_field[0]):
                field = matched_field[0].split('.')
            else:
                field = matched_field
        else:
            field = block_text_array

        if matched_field and hasattr(record, field[0]):
            image = getattr(record, field[0], b'')
            if isinstance(image, bytes):
                image = base64_to_image(image)
            else:
                if isinstance(image, str):
                    image = self.barcode('Code128', image)
                    image = base64_to_image(base64.b64encode(image).decode('utf-8'))
                else:
                    image = base64_to_image(getattr(image, field[1], b''))
            tempfile_png = tempfile.NamedTemporaryFile(suffix='.png')
            image.save(tempfile_png.name)
            block.text = ''
            if isinstance(block, _Cell):
                block = block.paragraphs[0]
            if len(field) == 3:
                block.add_run().add_picture(tempfile_png.name, width=Inches(int(field[1])))
            elif len(field) == 4:
                if field[2] == 'cm':
                    width = int(field[1]) / 2.54
                elif field[2] == 'mm':
                    width = int(field[1]) / 25.4
                elif field[2] == 'px':
                    width = int(field[1]) / 96
                else:
                    width = int(field[1])
                block.add_run().add_picture(tempfile_png.name, width=Inches(width))
            elif len(field) == 5:
                if field[3] == 'cm':
                    width = int(field[2]) / 2.54
                elif field[3] == 'mm':
                    width = int(field[2]) / 25.4
                elif field[3] == 'px':
                    width = int(field[2]) / 96
                else:
                    width = int(field[2])
                block.add_run().add_picture(tempfile_png.name, width=Inches(width))
            else :
                block.add_run().add_picture(tempfile_png.name)
        else:
            if matched_field:
                childs = block.text.split('.')
                block.text = ''
                data_ids = getattr(record, childs[2], b'')
                for data in data_ids:
                    if data.id == int(childs[0]):
                        if childs[1] == 'line_fix':
                            image = base64_to_image(getattr(data, childs[5], b''))
                            tempfile_png = tempfile.NamedTemporaryFile(suffix='.png')
                            image.save(tempfile_png.name)
                            if isinstance(block, _Cell):
                                block = block.paragraphs[0]
                            if childs[7] == 'width':
                                block.add_run().add_picture(tempfile_png.name, width=Inches(int(childs[4])))
                            elif childs[8] == 'width':
                                if childs[7] == 'cm':
                                    width = int(field[5]) / 2.54
                                elif childs[7] == 'mm':
                                    width = int(field[5]) / 25.4
                                elif childs[7] == 'px':
                                    width = int(field[5]) / 96
                                else:
                                    width = int(field[5])
                                block.add_run().add_picture(tempfile_png.name, width=Inches(width))
                            else:
                                block.add_run().add_picture(tempfile_png.name)
                            break
                        else:
                            image = base64_to_image(getattr(data, childs[3], b''))
                            tempfile_png = tempfile.NamedTemporaryFile(suffix='.png')
                            image.save(tempfile_png.name)
                            if isinstance(block, _Cell):
                                block = block.paragraphs[0]
                            if childs[5] == 'width':
                                block.add_run().add_picture(tempfile_png.name, width=Inches(int(childs[4])))
                            elif childs[6] == 'width':
                                if childs[5] == 'cm':
                                    width = int(field[4]) / 2.54
                                elif childs[5] == 'mm':
                                    width = int(field[4]) / 25.4
                                elif childs[5] == 'px':
                                    width = int(field[4]) / 96
                                else:
                                    width = int(field[4])
                                block.add_run().add_picture(tempfile_png.name, width=Inches(width))
                            else:
                                block.add_run().add_picture(tempfile_png.name)
                            break
                    else:
                        data = getattr(data, childs[3], '')
                        if data.id == int(childs[0]):
                            image = base64_to_image(getattr(data, childs[4], b''))
                            tempfile_png = tempfile.NamedTemporaryFile(suffix='.png')
                            image.save(tempfile_png.name)
                            if isinstance(block, _Cell):
                                block = block.paragraphs[0]
                            if childs[6] == 'width':
                                block.add_run().add_picture(tempfile_png.name, width=Inches(int(childs[4])))
                            elif childs[7] == 'width':
                                if childs[6] == 'cm':
                                    width = int(field[5]) / 2.54
                                elif childs[6] == 'mm':
                                    width = int(field[5]) / 25.4
                                elif childs[6] == 'px':
                                    width = int(field[5]) / 96
                                else:
                                    width = int(field[5])
                                block.add_run().add_picture(tempfile_png.name, width=Inches(width))
                            else:
                                block.add_run().add_picture(tempfile_png.name)
                            break


    def _replace_table_cell_with_image(self, table, record, fields):
        for (i, row) in enumerate(table.rows):
            for (j, cell) in enumerate(row.cells):
                self._match_and_replace(cell, record, fields)

