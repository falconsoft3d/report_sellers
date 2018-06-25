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

class WizardDebtReportDay(models.TransientModel):
    _name = 'wizard.debt.report.day'
    _description = 'Reporte Cuentas'

    @api.model
    def _get_default_start_date(self):
        date = fields.Date.from_string(fields.Date.today())
        start = '%s-%s-01'%(date.year, str(date.month).zfill(2))
        return start
    type_report = fields.Selection(
        [('1', 'Ventas'),
         ('2', 'Compras')],
        'Tipo de Reporte', size=1, default='2')
    report_date = fields.Date(string='Fecha',  default=lambda self: date.today(), help="Fecha")

    detail = fields.Boolean("Imprimir Detallado")
    
    @api.multi
    def print_xls(self):
        workbook = xlwt.Workbook(encoding="utf-8")
        style_title = xlwt.easyxf("font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
        currency = xlwt.easyxf('font: height 180; align: wrap yes, horiz right',num_format_str='$#0')
        budget_name = "Reporte"
        budget_name2 = "Reporte"
        today = datetime.today().strftime("%d-%m-%Y")
        worksheet = workbook.add_sheet(budget_name)
        k=1;i=2
        worksheet.write_merge(k, k, i, i, 'Fecha', )
        worksheet.write_merge(k, k, i+1, i+1, today, )
        k=2;i=2
        worksheet.write_merge(k, k,i, i+3, "Resumen por Día, al "+str(self.report_date), style_title )
        k=3;i=2
        worksheet.write_merge(k, k, i, i, 'Vencimiento', style_title)
        worksheet.write_merge(k, k, i+1, i+1, 'Cant. de Documentos', style_title)
        worksheet.write_merge(k, k, i+2, i+2, 'Monto', style_title)
        worksheet.write_merge(k, k, i+3, i+3, 'Acumulado', style_title)
        if self.detail:
            worksheet.write_merge(k, k, i+4, i+4, 'Nro', style_title)
            worksheet.write_merge(k, k, i+5, i+5, 'Partner', style_title)
            worksheet.write_merge(k, k, i+6, i+6, 'Total', style_title)
        obj_inv = self.env['account.invoice']
        if self.type_report == '1':
            invoice_expired_ids = obj_inv.search([
                ('state', '=', 'open'),('type',"=",'out_invoice')])
        else:
            invoice_expired_ids = obj_inv.search([
                ('state', '=', 'open'),('type',"=",'in_invoice')])
        total = 0
        dates = [((i.date_due != False and i.date_due >= self.report_date and i.date_due) or \
                (i.date_due == False and i.date >= self.report_date and i.date)) for i in invoice_expired_ids] 
        dates_list = list(set(dates))
        dates_list.remove(False)
        unaLista = dates_list
        for numPasada in range(len(dates_list)-1,0,-1):
            for i in range(numPasada):
                if dates_list[i]>dates_list[i+1]:
                    temp = dates_list[i]
                    dates_list[i] = dates_list[i+1]
                    dates_list[i+1] = temp
        row_index = 4
        for date in dates_list:
            sub_total = 0
            cont_documen = 0
            inv_sale_exp = invoice_expired_ids.filtered(lambda i:\
                (i.date_due == False and i.date == date) or \
                (i.date_due != False and i.date_due == date))
            for inv in inv_sale_exp:
                if inv.residual != inv.amount_total:
                    sub_total += inv.residual
                else:
                    sub_total += inv.amount_total
            total += sub_total 
            worksheet.write(row_index, 2, date, )
            worksheet.write(row_index, 3, len(inv_sale_exp), )
            worksheet.write(row_index, 4, sub_total, currency)
            worksheet.write(row_index, 5, total, currency)
            row_index += 1
            if self.detail:
                for inv in inv_sale_exp:
                    s_total = 0
                    if inv.residual != inv.amount_total:
                        s_total = inv.residual
                    else:
                        s_total = inv.amount_total
                    worksheet.write(row_index, 6, inv.number_folio, )
                    worksheet.write(row_index, 7, inv.partner_id.name,)
                    worksheet.write(row_index, 8, s_total, currency)
                    row_index += 1
        worksheet.col(2).width = 3000
        worksheet.col(3).width = 5000
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
        

