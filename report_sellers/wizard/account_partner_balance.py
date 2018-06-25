# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class WizardAccountPartnerBalance(models.TransientModel):
   
    _name = 'wizard.account.partner.balance'
    _description = 'Wizard that opens the information.'
    
    partner_id = fields.Many2one('res.partner', string='Cliente')
    type_report = fields.Selection(
        [('one','Por Cliente'),
         ('all','Todos los Clientes'),
         ],"Seleccione",default='one')

        
    def print_report(self, data):
        data.update(self.read(['partner_id', 'type_report'])[0])
        return self.env['report'].get_action(self, 'l10n_cl_debt_report.report_account_partner_balance', data=data)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
