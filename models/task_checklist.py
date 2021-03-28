from odoo import api, models, fields, exceptions, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.depends('checklist_item_ids', 'checklist_item_ids.done', 'checklist_item_ids.weight')
    def compute_checklist_stats(self):
        """:return the value for the check list progress"""
        for rec in self:
            total_items = rec.checklist_item_ids
            done_items = rec.checklist_item_ids.filtered('done')
            total_weight = sum(total_items.mapped('weight'))
            if total_weight:  # constrains are checked at create time so it is possible to have zero weight at run time
                rec.checklist_progress = sum(done_items.mapped('weight')) / total_weight * 100
            rec.checklist_items_count = len(total_items)
            rec.checklist_done_items_count = len(done_items)

    checklist_item_ids = fields.One2many('task_checklist.item', 'task_id', string='Check List')
    checklist_progress = fields.Float(compute='compute_checklist_stats', string='Weighted progress', store=True)
    checklist_items_count = fields.Integer(compute='compute_checklist_stats', string='Total Checklist Items',
                                           store=True)
    checklist_done_items_count = fields.Integer(compute='compute_checklist_stats', string='Done Checklist Items',
                                                store=True)
    use_deliverables = fields.Boolean(related='project_id.use_deliverables')


class CheckListItem(models.Model):
    _name = 'task_checklist.item'
    _description = 'Checklist for tasks'

    name = fields.Char(string='Description', required=True)
    weight = fields.Float(default=1)
    done = fields.Boolean(default=False)
    sequence = fields.Integer()
    task_id = fields.Many2one('project.task')

    _sql_constraints = [
        ('name_task_uniq', 'unique (name,task_id)', "Checklist item should be unique!"),
    ]

    @api.constrains('weight')
    def _check_weight(self):
        if self.filtered(lambda item: item.weight <= 0):
            raise exceptions.ValidationError(_('Weight of a checklist item should be positive.'))
