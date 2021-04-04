from odoo import api, models, fields, exceptions, _


class DeliverableItem(models.Model):
    _name = 'deliverable.item'
    _description = 'Deliverable Items'

    name = fields.Char(string='Description', required=True)
    weight = fields.Float(compute='_compute_weight', store=True, readonly=False)
    normal_weight = fields.Float(compute='_compute_normal_weight', store=True)
    done = fields.Boolean(default=False)
    sequence = fields.Integer()
    task_id = fields.Many2one('project.task')
    project_id = fields.Many2one('project.project', related='task_id.project_id', store=True)
    use_deliverables_weighting = fields.Boolean(related='project_id.use_deliverables_weighting')
    deliverables_weighting_method = fields.Selection(related='project_id.deliverables_weighting_method')

    _sql_constraints = [
        ('name_task_uniq', 'unique (name,task_id)', "Deliverable items should be unique!"),
    ]

    @api.constrains('weight')
    def _check_weight(self):
        if self.filtered(lambda item: item.weight <= 0):
            raise exceptions.ValidationError(_('Weight of a deliverable item should be positive.'))

    @api.depends('use_deliverables_weighting')
    def _compute_weight(self):
        for deliverable in self:
            if not deliverable.use_deliverables_weighting:
                deliverable.weight = 1

    @api.depends('weight', 'deliverables_weighting_method')
    def _compute_normal_weight(self):
        projects_sum_deliverable_weight = self.read_group(domain=[('project_id', 'in', self.mapped('project_id.id'))],
                                                          fields=['project_id', 'weight:sum(weight)'],
                                                          groupby=['project_id'])
        projects_sum_deliverable_weight_dict = dict()
        for item in projects_sum_deliverable_weight:
            projects_sum_deliverable_weight_dict[item['project_id'][0]] = item['weight']

        for deliverable in self:
            if deliverable.task_id.deliverables_weighting_method == 'within_task':
                deliverable.normal_weight = deliverable.weight / sum(
                    deliverable.task_id.deliverable_item_ids.mapped('weight'))
            else:
                deliverable.normal_weight = deliverable.weight / projects_sum_deliverable_weight_dict[
                    deliverable.project_id.id]
