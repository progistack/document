from odoo import fields, models, api

class Employee_sudo(models.Model):
	_name = 'hr.employee.sudo'
	_rec_name = 'employee_name'

	employee_id = fields.Many2one('hr.employee')
	employee_name = fields.Char("Nom employé")
	employee_email = fields.Char("Email employé")


class HrEmployeeInherit(models.Model):
	_inherit = 'hr.employee'

	def write(self, vals):

		for s in self:
			res = super(HrEmployeeInherit, self).write(vals)
			print("res", vals)
			if 'work_email' in vals:
				emp = self.env['hr.employee'].sudo().browse(s.id)
				emps = self.env['hr.employee.sudo'].search([('employee_id', '=', emp.id)])
				if not emps:
					emps.create({
							'employee_id': emp.id,
							'employee_name': emp.name,
							'employee_email': emp.work_email,
						})
				else:
					emps[0].write({
						'employee_name': emp.name,
						'employee_email': emp.work_email,
						})

		return True