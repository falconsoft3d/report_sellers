# -*- encoding: utf-8 -*-

import xlwt
import base64
import re
from cStringIO import StringIO
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import xlsxwriter



class WizardReportSellers(models.TransientModel):
    _name = 'wizard.report.sellers'
    _description = 'Reporte de Vendedores'
    
    @api.multi
    def print_xlsx(self):
        workbook = xlwt.Workbook(encoding="utf-8")
        style_title = xlwt.easyxf("font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
        currency = xlwt.easyxf('font: height 180; align: wrap yes, horiz right',num_format_str='$#0')
        percent = xlwt.easyxf('font: height 180; align: wrap yes, horiz right',num_format_str='#0%')
        budget_name = "Reporte de Vendedores"
        budget_name2 = "Reporte de Vendedores"
        today = datetime.today().strftime("%d-%m-%Y")
        worksheet = workbook.add_sheet(budget_name)
        k=3;j=2
        worksheet.write_merge(k, k, j, j, 'Fecha', )
        worksheet.write_merge(k, k, j+1, j+1, today, )
        k=4;j=2
        worksheet.write_merge(k, k, j, j, 'Folio', style_title)
        # worksheet.write_merge(k, k, j+1, j+1, 'Codigo', style_title)
        worksheet.write_merge(k, k, j+1, j+1, 'Tipo', style_title)
        worksheet.write_merge(k, k, j+2, j+2, 'Neto', style_title)
        worksheet.write_merge(k, k, j+3, j+3, 'Costo Total', style_title)
        worksheet.write_merge(k, k, j+4, j+4, 'Cant', style_title)
        worksheet.write_merge(k, k, j+5, j+5, 'Margen', style_title)
        worksheet.write_merge(k, k, j+6, j+6, 'Margen %', style_title)
        worksheet.write_merge(k, k, j+7, j+7, 'Vendedor', style_title)
        obj_inv = self.env['account.invoice']
        obj_users = self.env['res.users']
        obj_product = self.env['product.product']
        invoice_ids = obj_inv.search([
            ('state', 'in', ['open','paid']),('type',"=",'out_invoice')])
        type_documents = [i.document_class_id.sii_code for i in invoice_ids]
        type_documents = list(set(type_documents))
        row_index=5;j=2
        for inv in invoice_ids:
            worksheet.write(row_index, j, inv.number_folio, )
            worksheet.write(row_index, j+1, inv.document_class_id.sii_code, )
            worksheet.write(row_index, j+2, inv.amount_untaxed, currency)
            worksheet.write(row_index, j+7, inv.user_id.name, )
            row_index +=1
            for l in inv.invoice_line_ids:
                amount_stan_t = l.product_id.standard_price*l.quantity
                amount_sel_t = l.price_unit*l.quantity
                margin = amount_sel_t - amount_stan_t
                if amount_stan_t > 0:
                    margin_percent = (margin*100/amount_stan_t)/100
                else:
                    margin_percent = 0
                # worksheet.write(row_index, j+1, l.product_id.default_code, )
                cad = ""
                if l.product_id.default_code and l.product_id.name:
                    cad = "(" + l.product_id.default_code + ") " + l.product_id.name
                worksheet.write(row_index, j+1, cad, )
                worksheet.write(row_index, j+2, amount_sel_t, currency)
                worksheet.write(row_index, j+3, amount_stan_t, currency)
                worksheet.write(row_index, j+4, l.quantity, )
                worksheet.write(row_index, j+5, margin, currency)
                worksheet.write(row_index, j+6, round(margin_percent * 100,2),)
                row_index += 1
        
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        data_b64 = base64.encodestring(data)
        doc = self.env['ir.attachment'].create({
            'name': '%s.xls'%(budget_name2),
            'datas': data_b64,
            'datas_fname': '%s.xls'%(budget_name2),
        })
        return {
                'type' : "ir.actions.act_url",
                'url': "web/content/?model=ir.attachment&id="+str(doc.id)+"&filename_field=datas_fname&field=datas&download=true&filename="+str(doc.name),
                'target': "self",
                'no_destroy': False,
        }
    @api.model
    def get_days(self, date_init, date_end):
        return (datetime.strptime(str(date_end), '%Y-%m-%d')-datetime.strptime(str(date_init), '%Y-%m-%d')).days
    
