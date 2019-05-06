openerp.itis_hr_attendance_extend = function (instance) {

    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var _lt = instance.web._lt;
    var actionManager = instance.web.ActionManager;
    
    instance.hr_attendance.AttendanceSlider.include({
    	do_update_attendance: function() {
    		var self = this;
            this.$el.hide();
            var employee = new instance.web.DataSetSearch(self, 'hr.employee', self.session.user_context, [
                ['user_id', '=', self.session.uid]
            ]);
            employee.read_slice(['id', 'name', 'state', 'last_sign', 'attendance_access']).then(function (res) {
                if (_.isEmpty(res) )
                    return;
                if (res[0].attendance_access === false){
                    return;
                }
                self.$el.show();
                self.employee = res[0];
                self.last_sign = instance.web.str_to_datetime(self.employee.last_sign);
                self.set({"signed_in": self.employee.state !== "absent"});
                if(self.employee.state !== "absent"){
                	self.do_sign_out();
                }else{
                	self.do_sign_in();
                }
            });
    	},
    	do_sign_in: function () {
    		var self = this;
    		var sign_in_obj = new instance.web.DataSet(self, 'sign.in.task');
    		sign_in_obj.call('create', [{
            	'analytic_account_id': false
            }]).done(function(result){
            	console.log("idddd',",result);
            	self.temp_wizard_id = result;
            	var action = {
	                type: 'ir.actions.act_window',
	                res_model: 'sign.in.task',
	                view_mode: 'form',
	                view_type: 'form',
	                res_id: result,
	                views: [[false, 'form']],
	                target: 'new',
	            }
	            var act_ = new actionManager().do_action(action, {
	                on_close: function() {
	                    self.read_values();
	                },
	            });
            });
        },
        read_values: function (){
        	var self = this;
        	console.log('thssiss',this.temp_wizard_id);
        	var sign_in_obj = new instance.web.DataSet(self, 'sign.in.task');
        	sign_in_obj.call("do_entry_timesheet", [[this.temp_wizard_id]]).done(function(result){
        		console.log('reeeeee',result);
        		if(result){
        			self.super_do_update_attendance(result);
        		}
        	});
        },
    	super_do_update_attendance: function (timesheet_id) {
            var self = this;
            var context = new instance.web.CompoundContext();
            context.add({'timesheet_id': timesheet_id})
            var hr_employee = new instance.web.DataSet(self, 'hr.employee');
            hr_employee.call('attendance_action_change', [
                [self.employee.id],
                context
            ]).done(function (result) {
                self.last_sign = new Date();
                self.set({"timesheet_id": timesheet_id})
                self.set({"signed_in": ! self.get("signed_in")});
            });
        },
        do_sign_out: function(){
        	var self = this;
        	var ts_obj = new instance.web.DataSet(self, "hr.analytic.timesheet");
        	var timesheet_id = self.get("timesheet_id");
    		console.log("self.last_sign",self.last_sign);
        	ts_obj.call("update_hours", [[timesheet_id], self.last_sign]).done(function (result){
        		console.log("rrrrr",result);
        		if(result){
        			self.super_do_update_attendance(timesheet_id);
        		}
        	});
        },
    });
    instance.hr_timesheet_sheet.WeeklyTimesheet.include({

		init_add_account: function() {
            var self = this;
            if (self.dfm)
                return;
            console.log("In my customize-------")
            self.$(".oe_timesheet_weekly_add_row").show();
            self.dfm = new instance.web.form.DefaultFieldManager(self);
            self.dfm.extend_field_desc({
                account: {
                    relation: "account.analytic.account",
                },
                service_desc:{
                    relation: "service.description",
                },
            });

//			Add a logic to add comment and service description fields
			self.service_desc_m2o = new instance.web.form.FieldMany2One(self.dfm, {
                attrs: {
                    name: "service_desc",
                    type: "many2one",
                    placeholder: _t("Select Service Description"),
                },
            });
            self.service_desc_m2o.prependTo(self.$(".oe_timesheet_weekly_add_row_service"));
			self.comment_char = new instance.web.form.FieldText(self.dfm, {
                attrs: {
                    name: "emp_comment",
                    type: "char",
                    placeholder: _t("Add comment"),
                },
            });
            self.comment_char.prependTo(self.$(".oe_timesheet_weekly_add_row_comment"));
//			END

            self.account_m2o = new instance.web.form.FieldMany2One(self.dfm, {
                attrs: {
                    name: "account",
                    type: "many2one",
                    domain: [
                        ['type','in',['normal', 'contract']],
                        ['state', '<>', 'close'],
                        ['use_timesheets','=',1],
                        ['id', 'not in', _.pluck(self.accounts, "account")],
                    ],
                    context: {
                        default_use_timesheets: 1,
                        default_type: "contract",
                    },
                    modifiers: '{"required": true}',
                },
            });
            self.account_m2o.prependTo(self.$(".oe_timesheet_weekly_add_row_account"));

            self.$(".oe_timesheet_weekly_add_row button").click(function() {
                var id = self.account_m2o.get_value();
                var service_desc_id = self.service_desc_m2o.get_value();
                var comment = self.comment_char.get_value();

                if (id === false) {
                    self.dfm.set({display_invalid_fields: true});
                    return;
                }
                var ops = self.generate_o2m_value();
                new instance.web.Model("hr.analytic.timesheet").call("multi_on_change_account_id", [[], [id],
                    new instance.web.CompoundContext({'user_id': self.get('user_id')})]).then(function(res) {
                    res = res[id];
                    var def = _.extend({}, self.default_get, res.value, {
                        name: self.description_line,
                        unit_amount: 0,
                        date: instance.web.date_to_str(self.dates[0]),
                        account_id: id,
						emp_comment: comment,
                        service_desc_id : service_desc_id,
                    });
                    ops.push(def);
                    self.set({"sheets": ops});
                });
            });
        },

    	initialize_content: function(){
    		var self = this;
    		var sheet_id = this.field_manager.datarecord.id;
//			Add a logic to get the holiday dates from the python function
    		new instance.web.Model("itis.holiday").call("get_holiday_date").then(function(results){
        		self.holiday = results;
			});

    		if(sheet_id){
    			new instance.web.Model("planned.hours").call("search_read", [[['sheet_id', '=', sheet_id]], ['sheet_date', 'duration']]).then(function(results){
        			results.sort(self.dynamicSort("sheet_date"));
        			self.planned_hours = results;
        		});
    		}else{
    			self.planned_hours = [];
    		}

    		this._super();
//    		new instance.web.Model("hr_timesheet_sheet.sheet").call("get_analytic_timesheet_data",[[sheet_id]]).then(function(results){
//        		console.log("RESULT-------",results)
//        		self.analytic_timesheet_data = results;
//			});
    	},
    	dynamicSort: function(property){
    		var sortOrder = 1;
    		if(property[0] === "-"){
    			sortOrder = -1;
    			property = property.substr(1);
    		}
    		return function(a,b){
    			var result = (a[property] < b[property]) ? -1 : (a[property] > b[property]) ? 1 : 0;
    			return result * sortOrder;
    		}
    	},
    	display_data: function(){
    		var self = this;
    		this._super();
    		var tot = 0.0;
    		var self = this;
            var day_tots = _.map(_.range(self.dates.length), function() { return 0 });
            var super_tot = 0;
            _.each(self.accounts, function(account) {
                var acc_tot = 0;
                _.each(_.range(self.dates.length), function(day_count) {
                    var sum = self.sum_box(account, day_count);
                    acc_tot += sum;
                    day_tots[day_count] += sum;
                    super_tot += sum;
                });
            });
            var count = 0;
            _.each(this.planned_hours, function(pln_hrs){
            	var overtime = day_tots[count]-pln_hrs.duration;
    			tot += pln_hrs.duration;
    			self.$('[data-pln-dt="' + pln_hrs.sheet_date + '"]').html(self.format_client(pln_hrs.duration));
    			self.$('[data-ovr-tm="' + pln_hrs.sheet_date + '"]').html(self.format_client(overtime));
    			count += 1;
    		});
    		var tot_ovr_tm = super_tot - tot;
    		self.$('.oe_ph_hrs_total').html(self.format_client(tot));
    		self.$('.oe_ovr_tm_total').html(self.format_client(tot_ovr_tm));
    	}
    });
    instance.web.form.FieldFloat.include({
    	render_value: function(){
    		if(this.options.from_itis){
    			cur_val = this.get_value();
    			var trf_lgt = this.$el.find(".itis_traffic_light");
    			if(trf_lgt.length === 0){
    				this.$el.append("<span class='itis_traffic_light'></span>")
    			}
    			if(cur_val <= 20.0 && cur_val >= -20.0){
    				this.$el.find(".itis_traffic_light").html("<div class='led-green'>&nbsp;&nbsp;&nbsp;&nbsp;</div><div class='led-yellow-off'>&nbsp;&nbsp;&nbsp;&nbsp;</div><div class='led-red-off'>&nbsp;&nbsp;&nbsp;&nbsp;</div>");
    			}
    			if((cur_val > 20.0 && cur_val < 39.99) || (cur_val >= -39.99 && cur_val < -20.0)){
    				this.$el.find(".itis_traffic_light").html("<div class='led-green-off'>&nbsp;&nbsp;&nbsp;&nbsp;</div><div class='led-yellow'>&nbsp;&nbsp;&nbsp;&nbsp;</div><div class='led-red-off'>&nbsp;&nbsp;&nbsp;&nbsp;</div>");
    			}
    			if(cur_val > 39.99 || cur_val < -39.99){
    				this.$el.find(".itis_traffic_light").html("<div class='led-green-off'>&nbsp;&nbsp;&nbsp;&nbsp;</div></div><div class='led-yellow-off'>&nbsp;&nbsp;&nbsp;&nbsp;</div></div><div class='led-red'>&nbsp;&nbsp;&nbsp;&nbsp;</div>");
    			}
    		}
    		this._super();
    	}
    });
};