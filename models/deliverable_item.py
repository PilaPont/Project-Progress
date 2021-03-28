from odoo import api, models, fields, exceptions, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.depends('deliverable_item_ids', 'deliverable_item_ids.done', 'deliverable_item_ids.weight')
    def compute_deliverables_stats(self):
        """:return the value for the deliverable items progress"""
        for rec in self:
            total_items = rec.deliverable_item_ids
            done_items = rec.deliverable_item_ids.filtered('done')
            total_weight = sum(total_items.mapped('weight'))
            if total_weight:  # constrains are checked at create time so it is possible to have zero weight at run time
                rec.deliverables_progress = sum(done_items.mapped('weight')) / total_weight * 100
            rec.deliverable_items_count = len(total_items)
            rec.done_deliverable_items_count = len(done_items)

    deliverable_item_ids = fields.One2many('deliverable.item', 'task_id', string='Check List')
    deliverables_progress = fields.Float(compute='compute_deliverables_stats', string='Weighted progress', store=True)
    deliverable_items_count = fields.Integer(compute='compute_deliverables_stats', string='Total Deliverable Items',
                                           store=True)
    done_deliverable_items_count = fields.Integer(compute='compute_deliverables_stats', string='Done Deliverable Items',
                                                store=True)
    use_deliverables = fields.Boolean(related='project_id.use_deliverables')


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
