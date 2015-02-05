# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class sale_order_line_bom(models.Model):
    _name='sale.order.line.bom'
    
    @api.one
    @api.onchange('main_product')
    def _get_product_unit(self):
        self.unit=self.main_product.uom_id.id
    
    @api.one
    @api.depends('paper_product','manufacture_size','print_machine')
    def _get_product_count(self):
        print "================in get product count"
        try:
            effective_paper_width=self.paper_product.product_width - (self.print_machine.edge_space*2) + self.print_machine.lap_bw_products
            effective_paper_height=self.paper_product.product_height - (self.print_machine.edge_space*2) + self.print_machine.lap_bw_products
            effective_manufacture_width=self.width + self.print_machine.lap_bw_products
            effective_manufacture_height=self.height + self.print_machine.lap_bw_products
            width_count=int(effective_paper_width/effective_manufacture_width)
            height_count=int(effective_paper_height/effective_manufacture_height)
            product_count=width_count*height_count
            self.product_count=product_count
        except:
            print "error encountered in get_product_count"
            
    @api.one
    @api.depends('paper_product')
    def _get_quantity_available(self):
        if self.paper_product:
            self.warehouse_qty = float(self.paper_product.virtual_available) - float(self.paper_product.incoming_qty)
        else:
             self.warehouse_qty = 0
             
             
    #---
    @api.one
    @api.depends('manufacture_size')
    def _onchange_size(self):
        if self.manufacture_size and self.manufacture_size <> 15:
            self.width = self.list_size[self.manufacture_size][0]
            self.height = self.list_size[self.manufacture_size][1]
        else:
            self.width = 0
            self.height = 0
    
    list_size = [
                 (0,0),(594,840),(420,594),(297,420),(210,297),(148,210),(105,148),(74,105),(52,74),(320,488),(85,54),(320,450),(225,320),
                 (90,50),(1188,841)
                 ]
    
    sale_order_line=fields.Many2one('sale.order.line')
    bom_category_id = fields.Many2one('product.category',string = _("Product Category"))
    main_product=fields.Many2one('product.product',string=_('Component'),required=True)
    quantity=fields.Float(string=_('Quantity'),required=True,default=1)
    unit=fields.Many2one('product.uom',required=True)
    manufacture_size = fields.Selection([(14,"A0 - size 1188x841 mm"),(1,'A1 - size 594x840 mm'),(2,'A2 - size 420x594 mm'),(3,'A3 - size 297x420 mm'),
                                         (4,'A4 - size 210x297 mm'),(5,'A5 - size 148x210 mm'),(6,'A6 - size 105x148 mm'),
                                         (7,'A7 - size 74x105 mm'),(8,'A8 - size 52x74 mm'),(9,'Padidintas SRA3 - size 320x488 mm'),
                                         (10,'Plastikinė kortelė - size 85x54 mm'),(11,'SRA3 - size 320x450 mm'),
                                         (12,'SRA4 - size 225x320 mm'),(13,'Vizitine 90x50 - 90x50 mm'),(15,'Custom Size')
                                         ],default=False)
    height = fields.Float(compute='_onchange_size',string=_('Height'),default = 0)
    width = fields.Float(compute='_onchange_size',string=_('Width'),default = 0)
    paper_id = fields.Many2one('product.template',string = _("Paper Type"))
    paper_product = fields.Many2one('product.product',string=_("Weight and dimensions"))
    warehouse_qty = fields.Float(compute='_get_quantity_available',string = _("Quantity Available in Stock"))
    print_machine = fields.Many2one('mrp.workcenter',String=_("Printing Machine"))
    product_count = fields.Float(compute='_get_product_count',string = _('Product Count on Chosen Paper'))
    color_paper = fields.Many2one('color.paper',string=_("Saturation"))
    
    additional_works=fields.One2many('additional.works','sale_order_line',string="Additional Works")
    bom_line=fields.Many2one('mrp.bom')
    
    
    @api.constrains('manufacture_size','product_count','quantity')
    def check_for_product_count(self):
        if self.quantity==0:
            raise Warning(('Product quantity cannot be zero .  Please revise the data entered in product-line "%s" and component "%s"') % (self.sale_order_line.product_id.name,self.main_product.name))
        if self.manufacture_size!=False and self.product_count == 0.0 :
            raise Warning(('Product count cannot be zero .  Please revise the data entered in product-line "%s" and component "%s"') % (self.sale_order_line.product_id.name,self.main_product.name))
        if self.manufacture_size!=False and self.product_count != 0.0 and self.print_machine.id==False :
            raise Warning(('Please choose a print machine in product-line "%s" and component "%s"') % (self.sale_order_line.product_id.name,self.main_product.name))
