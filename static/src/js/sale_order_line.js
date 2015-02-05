openerp.gsp2= function (instance) {
    var _t = instance.web._t;
    var _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.gsp2 = instance.web.gsp2|| {};

    instance.gsp2.sale_order_line = instance.web.form.FormWidget.extend({
    
	    init: function (field_manager, node) {
		    this._super(field_manager, node);
	    },
		
		start:function() {
			 this._super();
			 var self = this;
			 self.field_manager.on("field_changed:is_manufacture",self,function(e){
				 self.field_manager.datarecord.is_manufacture = !self.field_manager.datarecord.is_manufacture ;
			 });
		},
    });
    instance.web.form.custom_widgets.add('sale_order_line', 'instance.gsp2.sale_order_line');

    instance.web.ListView.include({
    	do_add_record: function () {
    		var self = this;
    		try{
	    		if (this.dataset && this.dataset.model == "sale.order.line"){
	                    if (this.dataset.parent_view.datarecord.is_manufacture)
	                    {
	                            d = null;
	                    }
	                    else {
	                            d = "bottom";
	                    }
	            }
	            else {
	                    d = this.editable();
	            }
	            if (d) {
	                this._super.apply(this, arguments);
	            } else {
	                var pop = new instance.web.form.SelectCreatePopup(this);
	                pop.select_element(
	                    self.o2m.field.relation,
	                    {
	                        title: _t("Create: ") + self.o2m.string,
	                        initial_view: "form",
	                        alternative_form_view: self.o2m.field.views ? self.o2m.field.views["form"] : undefined,
	                        create_function: function(data, options) {
	                            return self.o2m.dataset.create(data, options).done(function(r) {
	                                self.o2m.dataset.set_ids(self.o2m.dataset.ids.concat([r]));
	                                self.o2m.dataset.trigger("dataset_changed", r);
	                            });
	                        },
	                        read_function: function() {
	                            return self.o2m.dataset.read_ids.apply(self.o2m.dataset, arguments);
	                        },
	                        parent_view: self.o2m.view,
	                        child_name: self.o2m.name,
	                        form_view_options: {'not_interactible_on_create':true}
	                    },
	                    self.o2m.build_domain(),
	                    self.o2m.build_context()
	                );
	                pop.on("elements_selected", self, function() {
	                    self.o2m.reload_current_view();
	                });
	            }
    		}
		catch (err){
			console.log("err:",err);
			this._super();
		}
    	}
	});
    
    instance.web.ListView.List.include({
    	row_clicked: function (event) {
    		var self = this;
    		if (this.dataset && this.dataset.model == "sale.order.line"){
                if (this.dataset.parent_view.datarecord.is_manufacture)
                {   
                	self.view.editable = function(){
                	return false;
                	}
                	return self._super.apply(self, arguments);
                }
    		}
    		this.view.editable = function(){
                return !this.grouped
                && !this.options.disable_editable_mode
                && (this.fields_view.arch.attrs.editable
                || this._context_editable
                || this.options.editable);
    		}

    		if (!this.view.editable() || ! this.view.is_action_enabled('edit')) {
                return this._super.apply(this, arguments);
            }
            var record_id = $(event.currentTarget).data('id');
            return this.view.start_edition(
                record_id ? this.records.get(record_id) : null, {
                focus_field: $(event.target).data('field')
            });    		
    		this._super(event);
    	},
    });
};
