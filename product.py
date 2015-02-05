# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class product_category(models.Model):
    _inherit = "product.category"
    _description = "gsp2 product category"
    
    is_paper = fields.Boolean('Paper Category')
    
    
class product_template(models.Model):
    _inherit='product.template'
    _description='Product Fields'
    
    @api.returns('product.uom')
    def get_mm_id(self):
        try:
            a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
            print 'a=======================',a
            return a
        except:
            print "error"
    
    
    product_width = fields.Float(related=('product_variant_ids','product_width'),string = _('Product Width'),required=True,default=0)
    width_uom=fields.Many2one(related=('product_variant_ids','width_uom'),default=get_mm_id)
    product_height = fields.Float(related=('product_variant_ids','product_height'),string = _('Product Height'),required=True,default=0)
    height_uom=fields.Many2one(related=('product_variant_ids','height_uom'),default=get_mm_id)
    product_weight = fields.Float(related=('product_variant_ids','product_weight'),string = _('Product Weight'),default=0)
    weight_uom=fields.Many2one(related=('product_variant_ids','weight_uom'))
    
    # writing fields that have to be carried over to product.product and 
    # readonly fields has to be written this way ...coz no value of them in vals    
    @api.model
    def create(self,vals):
        #print "vals======= p.t.c",vals
        a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
        product_template_id=super(product_template,self).create(vals)
        #print "===========here before write of measurements"
        product_template_id.write({'check':True,'product_width':vals.get('product_width',0),'product_height':vals.get('product_height',0),'product_weight':vals.get('product_weight',0),'width_uom':vals.get('width_uom',a),'height_uom':vals.get('height_uom',a),'weight_uom':vals.get('weight_uom',False)})
        return product_template_id
    
    
    
    
class product_product(models.Model):
    _inherit="product.product"
    _description="product.product changes"
    
    
    @api.returns('product.uom')
    def get_mm_id(self):
        try:
            a = self.env["ir.model.data"].get_object_reference("gsp2","product_uom_mm")[1]
            if a:return a
            else:return 1
        except:
            print "error"
    
    product_width = fields.Float(string = _('Product Width'),required=True,default=0)
    width_uom=fields.Many2one('product.uom',default=get_mm_id)
    product_height = fields.Float(string = _('Product Height'),required=True,default=0)
    height_uom=fields.Many2one('product.uom',default=get_mm_id)
    product_weight = fields.Float(string = _('Product Weight'),default=0)
    weight_uom=fields.Many2one('product.uom',default=get_mm_id)
    
    #changes name_get only in sale order line form in sale order 
    @api.multi
    @api.model
    def name_get(self):
        #print "in name_get product.product"
        result = []
        if self._context.get('search_default_product_tmpl_i',False):
            for product in self:
                result.append((product.id,"%s%s,%s%sx%s%s"%(product.product_weight,product.weight_uom.name,product.product_width,product.width_uom.name,product.product_height,product.height_uom.name)))
            return result
        return super(product_product,self).name_get()
    
    
    
    
    