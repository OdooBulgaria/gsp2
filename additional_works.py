# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class additional_works(models.Model):
    _name='additional.works'
    _description="additional works workcenter and product in sale order line"
    product=fields.Many2one('product.product',"Additional Works", required=True)
    workcenter=fields.Many2one('mrp.workcenter',"Workcenter", required=True)
    sequence = fields.Integer("Sequence",default=1)
    sale_order_line=fields.Many2one('sale.order.line')
    sale_order_line_bom=fields.Many2one('sale.order.line.bom')
    cycle_nbr=fields.Float("Number of cycles", required=True,help="Number of iterations this work center has to do in the specified operation of the routing.")
    hour_nbr= fields.Float('Number of Hours', required=True, help="Time in hours for this Work Center to achieve the operation of the specified routing.")
    