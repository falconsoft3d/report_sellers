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

class WizardDebtReport(models.TransientModel):
    _name = 'wizard.debt.report'
    _description = 'Reporte Cuentas'

    @api.model
    def _get_default_start_date(self):
        date = fields.Date.from_string(fields.Date.today())
        start = '%s-%s-01'%(date.year, str(date.month).zfill(2))
        return start
    report_date = fields.Date(string='Fecha',  default=lambda self: date.today(), help="Fecha")
    
    type_org = fields.Selection(
        [('1', 'Partner'),
         ('2', 'Vendedor/Comprador')],
        'Organizado', size=1, default='1')

    type_report = fields.Selection(
        [('1', 'Ventas'),
         ('2', 'Compras')],
        'Tipo de Reporte', size=1, default='2')
    cycle_days = fields.Integer(default = 30, string= "Longitud del período (días)")


    @api.multi
    def print_xlsx(self):
        workbook = xlwt.Workbook(encoding="utf-8")
        style_title = xlwt.easyxf("font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
        currency = xlwt.easyxf('font: height 180; align: wrap yes, horiz right',num_format_str='$#0')
        budget_name = "Reporte"
        budget_name2 = "Reporte"
        today = datetime.today().strftime("%d-%m-%Y")
        
        columns = ['VENCIDOS','VALORES POR VENCER']
        for i in range(1, 13):
            if i==6 or i==12:
                columns.append("Total")
            if i<6 :
                columns.append(str(self.cycle_days*(i-1))+"-"+str(self.cycle_days*i))
            elif i>6 and i<12:
                columns.append(str(self.cycle_days*(i-7))+"-"+str(self.cycle_days*(i-6)))
        worksheet = workbook.add_sheet(budget_name)
        j=1
        k=4
        for i, fieldname in enumerate(columns):
            if i == 0:
                worksheet.write_merge(3, 3, 2, 7, fieldname, style_title)
            elif i == 1:
                if self.type_org == '1':
                    worksheet.write_merge(k, k, i, i, 'PARTNER', )
                if self.type_org == '2' and self.type_report == '2':
                    worksheet.write_merge(k, k, i, i, 'COMPRADOR', )
                if self.type_org == '2' and self.type_report == '1':
                    worksheet.write_merge(k, k, i, i, 'VENDEDOR', )
                worksheet.write_merge(3, 3, 8, 13, fieldname, style_title)
            else :
                if i==13:
                    worksheet.write_merge(k, k, i+1, i+1, 'TOTAL', )
                worksheet.write_merge(k, k, i, i, fieldname,)
        
        obj_inv = self.env['account.invoice']

        invoice_expired_ids = obj_inv.search([('date_due',"<",self.report_date),('state', 'in', ['open', 'paid'])])
        invoice_by_expire_ids = obj_inv.search([('date_due',">=",self.report_date),('state', 'in', ['open', 'paid'])])
        
        inv_purchase_exp = invoice_expired_ids.filtered(lambda inv: inv.type == 'in_invoice')
        inv_sale_exp = invoice_expired_ids.filtered(lambda inv: inv.type == 'out_invoice')

        filter = self.type_org == '1' and 'partner_id' or 'user_id'

        supplier = [i.partner_id.id for i in inv_purchase_exp] 
        customer = [i.partner_id.id for i in inv_sale_exp] 
        codes_supplier = list(set(supplier))
        codes_customer = list(set(customer))
        
        if self.type_org == '1':
            if self.type_report == '1':
                partner_ids = self.env['res.partner'].search([('active',"=",True),('customer',"=",True)])
            else:
                partner_ids = self.env['res.partner'].search([('active',"=",True),('supplier',"=",True)])
            row_index=5
            for partner in partner_ids:
                
                t1 = 0;t2 = 0;t3 = 0;t4 = 0;t5 = 0;t6 = 0
                p1 = 0;p2 = 0;p3 = 0;p4 = 0;p5 = 0;p6 = 0  
                total = 0
                if self.type_report == '1':
                    invoice_expired_ids = self.env['account.invoice'].search(
                        [('partner_id',"=",partner.id),('date_invoice',"<",self.report_date),
                        ('type',"=",'out_invoice'),('state', 'in', ['open', 'paid'])])
                else:
                    invoice_expired_ids = self.env['account.invoice'].search(
                        [('partner_id',"=",partner.id),('date_invoice',"<",self.report_date),
                        ('type',"=",'in_invoice'),('state', 'in', ['open', 'paid'])])
                for invoice in invoice_expired_ids:
                    if invoice.date_due != False and invoice.date_due<self.report_date:
                        days = self.get_days(invoice.date_due,self.report_date)
                        if int(days) <= self.cycle_days:
                            t1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            t2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            t3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            t4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            t5 += invoice.amount_total
                        t6 = t1+t2+t3+t4+t5
                    elif invoice.date_due == False and invoice.date_invoice<self.report_date:
                        days = self.get_days(invoice.date,self.report_date)
                        if int(days) <= self.cycle_days:
                            t1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            t2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            t3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            t4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            t5 += invoice.amount_total
                        t6 = t1+t2+t3+t4+t5
                if self.type_report == '1':
                    invoice_by_expire_ids = self.env['account.invoice'].search(
                        [('partner_id',"=",partner.id),('date_invoice',">=",self.report_date),
                        ('type',"=",'out_invoice'),('state', 'in', ['open', 'paid'])])
                else:
                    invoice_by_expire_ids = self.env['account.invoice'].search(
                        [('partner_id',"=",partner.id),('date_invoice',">=",self.report_date),
                        ('type',"=",'in_invoice'),('state', 'in', ['open', 'paid'])])
                for invoice in invoice_by_expire_ids:
                    if invoice.date_due != False and invoice.date_due>=self.report_date:
                        days = self.get_days(self.report_date,invoice.date_due)
                        if int(days) <= self.cycle_days:
                            p1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            p2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            p3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            p4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            p5 += invoice.amount_total
                        p6 = p1+p2+p3+p4+p5
                    
                    elif invoice.date_due == False and invoice.date_invoice>=self.report_date:
                        days = self.get_days(self.report_date,invoice.date)
                        if int(days) <= self.cycle_days:
                            p1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            p2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            p3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            p4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            p5 += invoice.amount_total
                        p6 = p1+p2+p3+p4+p5
                        
                total = t6+p6
                if total !=0:
                    
                    worksheet.write(row_index, 1, partner.name+" ("+str(partner.document_number)+")", )
                    worksheet.write(row_index, 2, t1, currency)
                    worksheet.write(row_index, 3, t2, currency)
                    worksheet.write(row_index, 4, t3, currency)
                    worksheet.write(row_index, 5, t4, currency)
                    worksheet.write(row_index, 6, t5, currency)
                    worksheet.write(row_index, 7, t6, currency)
                    worksheet.write(row_index, 8, p1, currency)
                    worksheet.write(row_index, 9, p2, currency)
                    worksheet.write(row_index, 10, p3, currency)
                    worksheet.write(row_index, 11, p4, currency)
                    worksheet.write(row_index, 12, p5, currency)
                    worksheet.write(row_index, 13, p6, currency)
                    worksheet.write(row_index, 14, total, currency)
                    row_index += 1
        
        else:
            if self.type_report == '1':
                user_ids = self.env['res.users'].search([('active',"=",True)])
            else:
                user_ids = self.env['res.users'].search([('active',"=",True)])
            row_index=5
            for user in user_ids:
                
                t1 = 0;t2 = 0;t3 = 0;t4 = 0;t5 = 0;t6 = 0
                p1 = 0;p2 = 0;p3 = 0;p4 = 0;p5 = 0;p6 = 0  
                total = 0
                if self.type_report == '1':
                    invoice_expired_ids = self.env['account.invoice'].search(
                        [('user_id',"=",user.id),('date_invoice',"<",self.report_date),
                        ('type',"=",'out_invoice'),('state', 'in', ['open', 'paid'])])
                else:
                    invoice_expired_ids = self.env['account.invoice'].search(
                        [('user_id',"=",user.id),('date_invoice',"<",self.report_date),
                        ('type',"=",'in_invoice'),('state', 'in', ['open', 'paid'])])
                for invoice in invoice_expired_ids:
                    if invoice.date_due != False and invoice.date_due<self.report_date:
                        days = self.get_days(invoice.date_due,self.report_date)
                        if int(days) <= self.cycle_days:
                            t1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            t2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            t3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            t4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            t5 += invoice.amount_total
                        t6 = t1+t2+t3+t4+t5
                    if invoice.date_due == False and invoice.date<self.report_date:
                        days = self.get_days(invoice.date,self.report_date)
                        if int(days) <= self.cycle_days:
                            t1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            t2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            t3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            t4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            t5 += invoice.amount_total
                        t6 = t1+t2+t3+t4+t5
                    
                if self.type_report == '1':
                    invoice_by_expire_ids = self.env['account.invoice'].search(
                        [('user_id',"=",user.id),('date_invoice',">=",self.report_date),
                        ('type',"=",'out_invoice'),('state', 'in', ['open', 'paid'])])
                else:
                    invoice_by_expire_ids = self.env['account.invoice'].search(
                        [('user_id',"=",user.id),('date_invoice',">=",self.report_date),
                        ('type',"=",'in_invoice'),('state', 'in', ['open', 'paid'])])
                
                for invoice in invoice_by_expire_ids:
                    if invoice.date_due != False and invoice.date_due>=self.report_date:
                        days = self.get_days(self.report_date,invoice.date_due)
                        if int(days) <= self.cycle_days:
                            p1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            p2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            p3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            p4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            p5 += invoice.amount_total
                        p6 = p1+p2+p3+p4+p5
                    if invoice.date_due == False and invoice.date>=self.report_date:
                        days = self.get_days(self.report_date,invoice.date)
                        if int(days) <= self.cycle_days:
                            p1 += invoice.amount_total
                        if int(days) > self.cycle_days and int(days) <= self.cycle_days*2:
                            p2 += invoice.amount_total
                        elif int(days) > self.cycle_days*2 and int(days) <= self.cycle_days*3:
                            p3 += invoice.amount_total
                        elif int(days) > self.cycle_days*3 and int(days) <= self.cycle_days*4:
                            p4 += invoice.amount_total
                        elif int(days) > self.cycle_days*4 and int(days) <= self.cycle_days*5:
                            p5 += invoice.amount_total
                        p6 = p1+p2+p3+p4+p5
                total = t6+p6
                if total !=0:
                    worksheet.write(row_index, 1, user.name, )
                    worksheet.write(row_index, 2, t1, currency)
                    worksheet.write(row_index, 3, t2, currency)
                    worksheet.write(row_index, 4, t3, currency)
                    worksheet.write(row_index, 5, t4, currency)
                    worksheet.write(row_index, 6, t5, currency)
                    worksheet.write(row_index, 7, t6, currency)
                    worksheet.write(row_index, 8, p1, currency)
                    worksheet.write(row_index, 9, p2, currency)
                    worksheet.write(row_index, 10, p3, currency)
                    worksheet.write(row_index, 11, p4, currency)
                    worksheet.write(row_index, 12, p5, currency)
                    worksheet.write(row_index, 13, p6, currency)
                    worksheet.write(row_index, 14, total, currency)
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



