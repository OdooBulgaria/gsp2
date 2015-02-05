# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import math

class sale_order_line(models.Model):
    _inherit="sale.order.line"
    _description = "gsp2 sale order line"
    
    @api.one
    @api.depends('state')
    def _cancel_sale_order_line(self):
        if self.state==cancel:
            print "state cancel in _cancel_sale_order_line=================="
            procurement=self.env['procurement.order'].search([('sale_line_id','=',self.id)])
            for proc in procurement:
                proc.cancel(self._cr,self._uid,[proc.id],self._context)
    
    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, warehouse_id=False, context=None):
        
        result =  super(sale_order_line, self).product_id_change_with_wh( cr, uid, ids, pricelist, product, qty,uom, qty_uos, uos, name, partner_id,lang, update_tax, date_order, packaging, fiscal_position, flag, warehouse_id=warehouse_id, context=context)
        if product:
            result['value'].update({'category_id':self.pool.get('product.product').browse(cr,uid,product).categ_id.id })
        return result
    
    @api.one
    @api.depends('paper_product','manufacture_size','print_machine','height','width')
    def _get_product_count(self):
        #print "================in get product count"
        if self.paper_product and (self.paper_product.product_width==0.0 or self.paper_product.product_height==0.0):
            raise Warning("Please set the measurements in the product inventory page of product %s"%(self.paper_product.name_template))
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
    
    
    category_id = fields.Many2one('product.category',string = _("Product Category"))
    is_multi_level = fields.Boolean(string=_("Does the product have multi-level BOM ?"))
    multi_level_bom=fields.One2many('sale.order.line.bom','sale_order_line')
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
    
    @api.constrains('manufacture_size','is_multi_level','product_count')
    def check_for_product_count(self):
        if self.is_multi_level==False and self.manufacture_size!=False and self.product_count == 0.0 :
            raise Warning(('Product count cannot be zero .  Please revise the data entered in product-line "%s" ') % (self.product_id.name))
        #print "==========",self.is_multi_level,self.manufacture_size,self.product_count,self.print_machine.id
        if self.is_multi_level==False and self.manufacture_size!=False and self.product_count != 0.0 and self.print_machine.id==False :
            raise Warning(('Please choose a print machine in product-line "%s" ') % (self.product_id.name))

    
    
    
    def button_confirm(self, cr, uid, ids, context=None):
        sale_lines=self.browse(cr,uid,ids)
        bom_obj=self.pool.get("mrp.bom")
        routing_obj=self.pool.get("mrp.routing")
        for line in sale_lines:
            if line.is_multi_level:
                property_id = self.pool.get("ir.model.data").get_object_reference(cr,uid,"gsp2","bom_property_SO")[1]
                sale_line_mrp_property_vals={'name':line.order_id.name+':'+line.product_id.name+' '+str(line.id),
                                                 'group_id':property_id,
                                                 'composition':'min',
                                                 }
                sale_line_mrp_property_id=[self.pool.get('mrp.property').create(cr,uid,sale_line_mrp_property_vals)]
                
                for component in line.multi_level_bom:
                    # making of rouitng and bom of the component in multi_level_bom 
                    if component.manufacture_size!=False and component.print_machine!=False and component.product_count!=0:
                        paper_amount=math.ceil(component.quantity/component.product_count)
    
                        routing_lines=[]
                        nbr_cycle_print_machine=math.ceil(paper_amount/component.print_machine.capacity_per_cycle)
                        print_line={"name":component.main_product.name,
                                    "sequence":1,
                                    "workcenter_id":component.print_machine.id,
                                    "cycle_nbr":nbr_cycle_print_machine
                                    }
                        routing_lines.append([0,0,print_line])
                        for rec in component.additional_works:
                            vals_routing_lines={"name":rec.product.name,
                                       "sequence":rec.sequence+1,
                                       "workcenter_id":rec.workcenter.id,
                                       "cycle_nbr":rec.cycle_nbr,
                                       "hour_nbr":rec.hour_nbr
                                       }
                            line_dict_12=[0,0,vals_routing_lines]
                            routing_lines.append(line_dict_12)
                        #print "==================routing_lines",routing_lines
                        
                        
                        vals_routing={"name":"Routing of Component:"+component.main_product.name+' of product-line '+component.sale_order_line.product_id.name,
                                      "active":False,
                                      "workcenter_lines":routing_lines
                                      }
                        #print "vals-routing============",vals_routing
                        routing_id=routing_obj.create(cr,uid,vals_routing,context)
                        
                        bom_lines={"product_id":component.paper_product.id,
                                   "type":'normal',
                                   "product_qty":paper_amount,
                                   "product_uom":component.paper_product.uom_id.id,
                                   "product_rounding":0.0,
                                   "product_efficiency":1.0,
                                   }
                        vals_bom={
                              "product_tmpl_id":component.main_product.product_tmpl_id.id,
                              "product_id":component.main_product.id,
                              "active":False,
                              "product_qty":component.quantity,
                              "product_uom":component.unit.id,
                              "bom_line_ids":[[0,0,bom_lines]],
                              "type":'normal',
                              "name":component.main_product.name+" BOM of "+component.sale_order_line.product_id.name+" product-line of"+component.sale_order_line.order_id.name,
                              "routing_id":routing_id,
                              "property_ids":[(6,0,sale_line_mrp_property_id)]
                              
                              }
                        
                        #print "vals_bom===============",vals_bom
                        bom_id=bom_obj.create(cr,uid,vals_bom,context)
                        self.pool.get('sale.order.line.bom').write(cr, uid, component.id, {'bom_line': bom_id})

                    
                
                # making of routing and BOM of the sale line ---BOM has components in it.
                routing_lines=[]
                for rec in line.additional_works:
                    vals_routing_lines={"name":rec.product.name,
                               "sequence":rec.sequence,
                               "workcenter_id":rec.workcenter.id,
                               "cycle_nbr":rec.cycle_nbr,
                               "hour_nbr":rec.hour_nbr
                               }
                    line_dict_12=[0,0,vals_routing_lines]
                    routing_lines.append(line_dict_12)
                #print "==================routing_lines",routing_lines
                vals_routing={"name":line.product_id.name+':'+line.order_id.name,
                              "active":False,
                              "workcenter_lines":routing_lines
                              }
                #print "vals-routing============",vals_routing
                routing_id=routing_obj.create(cr,uid,vals_routing,context)
                
                
                    
                bom_lines=[]
                for component in line.multi_level_bom:
                    bom_lines_dict={"product_id":component.main_product.id,
                               "type":'normal',
                               "product_qty":component.quantity,
                               "product_uom":component.unit.id,
                               "product_rounding":0.0,
                               "product_efficiency":1.0,
                               }
                    bom_lines.append([0,0,bom_lines_dict])
                
                vals_bom={
                          "product_tmpl_id":line.product_id.product_tmpl_id.id,
                          "product_id":line.product_id.id,
                          "active":False,
                          "product_qty":line.product_uom_qty,
                          "product_uom":line.product_uom.id,
                          "bom_line_ids":bom_lines,
                          "type":'normal',
                          "name":line.product_id.name+':'+line.order_id.name,
                          "routing_id":routing_id,
                          "property_ids":[(6,0,sale_line_mrp_property_id)]
                          }
                
                #print "vals_bom===============",vals_bom
                bom_id=bom_obj.create(cr,uid,vals_bom,context)
                self.write(cr, uid, line.id, {'bom_line': bom_id,'property_ids': [(6,0,sale_line_mrp_property_id)]})
            
            else:
                if line.manufacture_size!=False and line.print_machine!=False and line.product_count!=0:
                    paper_amount=math.ceil(line.product_uom_qty/line.product_count)

                    routing_lines=[]
                    nbr_cycle_print_machine=math.ceil(paper_amount/line.print_machine.capacity_per_cycle)
                    print_line={"name":line.product_id.name,
                                "sequence":1,
                                "workcenter_id":line.print_machine.id,
                                "cycle_nbr":nbr_cycle_print_machine
                                }
                    routing_lines.append([0,0,print_line])
                    for rec in line.additional_works:
                        vals_routing_lines={"name":rec.product.name,
                                   "sequence":rec.sequence+1,
                                   "workcenter_id":rec.workcenter.id,
                                   "cycle_nbr":rec.cycle_nbr,
                                   "hour_nbr":rec.hour_nbr
                                   }
                        line_dict_12=[0,0,vals_routing_lines]
                        routing_lines.append(line_dict_12)
                    #print "==================routing_lines",routing_lines
                    
                    
                    vals_routing={"name":line.product_id.name+':'+line.order_id.name,
                                  "active":False,
                                  "workcenter_lines":routing_lines
                                  }
                    #print "vals-routing============",vals_routing
                    routing_id=routing_obj.create(cr,uid,vals_routing,context)
                    
                    bom_lines={"product_id":line.paper_product.id,
                               "type":'normal',
                               "product_qty":paper_amount,
                               "product_uom":line.paper_product.uom_id.id,
                               "product_rounding":0.0,
                               "product_efficiency":1.0,
                               }
                    
                    property_id = self.pool.get("ir.model.data").get_object_reference(cr,uid,"gsp2","bom_property_SO")[1]
                    sale_line_mrp_property_vals={'name':line.order_id.name+':'+line.product_id.name+' '+str(line.id),
                                                 'group_id':property_id,
                                                 'composition':'min',
                                                 }
                    sale_line_mrp_property_id=[self.pool.get('mrp.property').create(cr,uid,sale_line_mrp_property_vals)]
                    
                    vals_bom={
                          "product_tmpl_id":line.product_id.product_tmpl_id.id,
                          "product_id":line.product_id.id,
                          "active":False,
                          "product_qty":line.product_uom_qty,
                          "product_uom":line.product_uom.id,
                          "bom_line_ids":[[0,0,bom_lines]],
                          "type":'normal',
                          "name":line.product_id.name+':'+line.order_id.name,
                          "routing_id":routing_id,
                          "property_ids":[(6,0,sale_line_mrp_property_id)]
                          }
                    
                    #print "vals_bom===============",vals_bom
                    bom_id=bom_obj.create(cr,uid,vals_bom,context)
                    self.write(cr, uid, line.id, {'bom_line': bom_id,'property_ids': [(6,0,sale_line_mrp_property_id)]})
        return super(sale_order_line,self).button_confirm(cr, uid, ids, context)
    
    

    
class sale_order(models.Model):
    _inherit='sale.order'
    _description='changes in sale'
    
    '''@api.multi
    def name_get(self):
        res = super(sale_order,self).name_get()
        print "in name_get of sale.order"
        print res
        return res'''
    
    
    
    @api.one
    @api.model
    def change_order_qty(self):
        for line in self.order_line:
            line.product_uom_qty = 1
    
    @api.multi
    def write(self,vals,context=None):
        result = super(sale_order,self).write(vals)
        if self.test_order:
            self.change_order_qty()
        return result
    
    @api.model
    def create(self,vals):
        #print "================vals sale_ordre",vals
        id = super(sale_order,self).create(vals)
        if id.test_order:
            id.change_order_qty()
        return id
    
    @api.onchange('test_order')
    def _onchange_quantity(self):
        for line in self.order_line:
            line.product_uom_qty = 1
    
    def do_view_po(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display the Purchase order related to this sales order
        '''
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        pro_obj=self.pool.get('procurement.order')
        result = mod_obj.get_object_reference(cr, uid, 'gsp2', 'do_view_po')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id in (select distinct procurement_group_id from sale_order where id in (%s)))',(ids))
        result_cr=cr.fetchall()
        print "query==============",result_cr
        ids=[i[0] for i in result_cr if i[0]]
        print "ids=========",ids
        result['domain'] = "[('id','in',[" + ','.join(map(str,ids)) + "])]"
        return result
        
            
    def do_view_mo(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display the Manufacturing order related to this sales order
        '''
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        pro_obj=self.pool.get('procurement.order')
        result = mod_obj.get_object_reference(cr, uid, 'gsp2', 'do_view_mo')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        
        cr.execute('select distinct production_id from procurement_order where group_id in (select distinct procurement_group_id from sale_order where id in (%s))',(ids))
        result_cr=cr.fetchall()
        print "query==============",result_cr
        ids=[i[0] for i in result_cr if i[0]]
        print "ids=========",ids
        result['domain'] = "[('id','in',[" + ','.join(map(str,ids)) + "])]"
        return result
        
            
    def do_view_pickings_sale(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display the pickings of the procurements belonging
        to the same procurement group of given ids.
        '''
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'gsp2', 'do_view_pickings_sale_action')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        group_ids = set([proc.procurement_group_id.id for proc in self.browse(cr, uid, ids, context=context) if proc.procurement_group_id])
        print "ids==================in  do_view_pickings",ids
        print "group_ids=====",group_ids
        print "type(group_ids)=====",type(group_ids)
        print "list(group_ids)========",list(group_ids)
        print "type(list(group_ids))========",type(list(group_ids))
        result['domain'] = "[('group_id','in',[" + ','.join(map(str, list(group_ids))) + "])]"
        return result
        
    @api.one
    @api.depends()
    def _count_all(self):
        cr=self._cr
        print "====================== in _count_all"
        group_id=[self.procurement_group_id and self.procurement_group_id.id]
        if group_id[0]:
            print "group_id==============",group_id
            cr.execute('select distinct production_id from procurement_order where group_id = (%s) and production_id is not null',(group_id))
            mo_count=cr.fetchall()
            print "mo_count============",mo_count
            self.mo_count=len(mo_count)
            
            cr.execute('select distinct order_id from purchase_order_line where id in (select distinct purchase_line_id from procurement_order where group_id = (%s) and group_id is not null) and order_id is not null',(group_id))
            po_count=cr.fetchall()
            print "po_count============",po_count
            self.po_count=len(po_count)
            
            cr.execute('select distinct id from stock_picking where group_id = (%s) and id is not null',(group_id))
            picking_count=cr.fetchall()
            print "picking_count============",picking_count
            self.picking_count=len(picking_count)
            
            
        
    is_manufacture = fields.Boolean(string='Manufacture',default=False)
    test_order = fields.Boolean('Test Order')
    priority = fields.Integer('Priority')
    po_count=fields.Integer(compute='_count_all',readonly=True)
    mo_count=fields.Integer(compute='_count_all',readonly=True)
    picking_count=fields.Char(compute='_count_all',readonly=True)