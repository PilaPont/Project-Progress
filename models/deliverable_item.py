from odoo import api, models, fields, exceptions, _


class DeliverableItem(models.Model):
    _name = 'deliverable.item'
    _description = 'Deliverable Items'

    name = fields.Char(string='Description', required=True)
    weight = fields.Float(default=1)
    done = fields.Boolean(default=False)
    sequence = fields.Integer()
    task_id = fields.Many2one('project.task')

    _sql_constraints = [
        ('name_task_uniq', 'unique (name,task_id)', "Deliverable items should be unique!"),
    ]

    @api.constrains('weight')
    def _check_weight(self):
        if self.filtered(lambda item: item.weight <= 0):
            raise exceptions.ValidationError(_('Weight of a deliverable item should be positive.'))
