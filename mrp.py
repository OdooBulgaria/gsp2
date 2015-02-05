# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import time
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp import tools, SUPERUSER_ID
from openerp.addons.product import _common



class mrp_bom(models.Model):
    _inherit='mrp.bom'
    
    def false_bom_find(self, cr, uid, product_tmpl_id=None, product_id=None, properties=None, context=None):
        if properties is None:
            properties = []
        if product_id:
            if not product_tmpl_id:
                product_tmpl_id = self.pool['product.product'].browse(cr, uid, product_id, context=context).product_tmpl_id.id
            domain = [
                '|',
                    ('product_id', '=', product_id),
                    '&',
                        ('product_id', '=', False),
                        ('product_tmpl_id', '=', product_tmpl_id)
            ]
        elif product_tmpl_id:
            domain = [('product_id', '=', False), ('product_tmpl_id', '=', product_tmpl_id)]
        else:
            # neither product nor template, makes no sense to search
            return False
        domain = domain + [ '|', ('date_start', '=', False), ('date_start', '<=', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                            '|', ('date_stop', '=', False), ('date_stop', '>=', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))]
        domain = domain + [('active','=',False)]
        # order to prioritize bom with product_id over the one without
        ids = self.search(cr, uid, domain, order='product_id', context=context)
        #print "=========ids===========",ids
        # Search a BoM which has all properties specified, or if you can not find one, you could
        # pass a BoM without any properties
        bom_empty_prop = False
        #print "domain=======",domain
        for bom in self.pool.get('mrp.bom').browse(cr, uid, ids, context=context):
            if set(map(int, bom.property_ids or [])) == set(properties or []):
                if properties:
                    bom_empty_prop = bom.id
        return bom_empty_prop

    
'''class stock_move(models.Model):
    _inherit="stock.move"
    
    def create(self,cr,uid,vals,context=None):
        if not context:context={}
        id=super(stock_move, self).create(cr,uid,vals,context)
        print "id****************stock_move",id
        print "vals**************stock_move",vals
        return id


class mrp_production(models.Model):
    _inherit="mrp.production"
    
    def create(self,cr,uid,vals,context=None):
        if not context:context={}
        id=super(mrp_production, self).create(cr,uid,vals,context)
        print "id****************mrp_production",id
        print "vals**************mrp_production",vals
        return id'''

class procurement_order(models.Model):
    _inherit='procurement.order'
    
    '''def create(self,cr,uid,vals,context=None):
        if not context:context={}
        id=super(procurement_order, self).create(cr,uid,vals,context)
        print "id****************procurement.order",id
        print "vals**************procurement.order",vals
        return id'''
    
    def make_mo(self, cr, uid, ids, context=None):
        res=super(procurement_order, self).make_mo(cr,uid,ids,context)
        production_obj = self.pool.get('mrp.production')
        procurement_obj = self.pool.get('procurement.order')
        for procurement in procurement_obj.browse(cr, uid, ids, context=context):
            if procurement.production_id:
                if procurement.property_ids:
                    property_ids_list=tuple(map(int, procurement.property_ids))   
                    print "============property_ids_list=======",property_ids_list
                    print "********************************************************"
                    print "select order_id from sale_order_line_property_rel where property_id in (%s);"%(property_ids_list)
                    cr.execute('select order_id from sale_order_line_property_rel where property_id in (%s)',(property_ids_list))
                    result=cr.fetchall()
                    print "************************cr.fetchall",result
                    if len(result)==1:
                        self.pool.get('sale.order.line').write(cr,uid,result[0][0],{'mo_id':procurement.production_id.id})
                        
        return res
    
    def check_bom_exists(self, cr, uid, ids, context=None):
        """ Finds the bill of material for the product from procurement order.
        @return: True or False
        """
        print "in check_bom_exists====================="
        for procurement in self.browse(cr, uid, ids, context=context):
            properties = [x.id for x in procurement.property_ids]
            print "checking procurement",procurement.product_id.name
            print "properties=========",properties
            print "procurement origin====",procurement.origin
            print "procurement production",procurement.production_id
            if properties==[]:
                mo=procurement.origin.split(':')[-1]
                print "mo===========split",mo
                domain=[('group_id','=',procurement.group_id.id)]
                ids_prop=self.search(cr,uid,domain,context=context)
                for procure in self.browse(cr, uid, ids_prop, context=context):
                    if procure.production_id.name==mo and procure.property_ids:
                        properties = [x.id for x in procure.property_ids]
                        if properties:
                            bom_id=self.pool.get('mrp.bom').false_bom_find(cr, uid, product_id=procurement.product_id.id,properties=properties, context=context)
                            if bom_id:
                                self.write(cr,uid,procurement.id,{'bom_id':bom_id})
                                return True
                                         
                        
                        
            else:
                properties = [x.id for x in procurement.property_ids]
                bom_id=self.pool.get('mrp.bom').false_bom_find(cr, uid, product_id=procurement.product_id.id,properties=properties, context=context)
                if bom_id:
                    self.write(cr,uid,procurement.id,{'bom_id':bom_id})
                    return True
            
        return super(procurement_order, self).check_bom_exists(cr,uid,ids,context)
    


class mrp_workcenter(models.Model):
    _inherit='mrp.workcenter'
    _description='Fields'
    
    @api.returns('product.uom')
    def get_mm_id(self):
        try:
            a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
            if a:return a
            else:return 1
        except:
            print "error"
    
    max_height=fields.Float(string=_("Maximum Height"))
    max_height_uom = fields.Many2one('product.uom',default=get_mm_id)
    max_width=fields.Float(string=_("Maximum Width"),required=True)
    max_width_uom = fields.Many2one('product.uom',default=get_mm_id)
    edge_space=fields.Float(string=_('Edge Space'))
    edge_uom=fields.Many2one('product.uom',default=get_mm_id)
    lap_bw_products=fields.Float(string=_("Lap Between Products"))
    lap_uom=fields.Many2one('product.uom',default=get_mm_id)
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        ids=super(mrp_workcenter,self).name_search(name=name,args=args,operator='ilike',limit=100)
        #print "====================",self._context.get('paper_product',False)
        if self._context.get('paper_product',False):
            #print "=====================",self._context.get('paper_product',False)
            obj=self.env['product.product'].browse(self._context.get('paper_product'))
            #print "obj",obj
            width=obj.product_width
            height=obj.product_height
            list=[]
            records=self.search([])
            for rec in records:
                #print "===============",rec
                if rec.max_height!=0 and rec.max_height>=height and rec.max_width>=width:
                    for name_wk in range(len(ids)):
                        if rec.id==ids[name_wk][0]:
                            list.append(ids[name_wk])
                if rec.max_height==0 and rec.max_width>=width:
                    for name_wk in range(len(ids)):
                        if rec.id==ids[name_wk][0]:
                            list.append(ids[name_wk])
            return list
        return ids
    
    @api.one
    @api.constrains('max_width','capacity_per_cycle')
    def force_width(self):
        #print "======================= force_width",self.max_width
        if self.max_width==0.0:
            #print "in warning"
            raise Warning("Please Set A Width For the Workcenter")
        if self.capacity_per_cycle==0.0:
            raise Warning("Please Set a capacity greater than 0")
    

    
    