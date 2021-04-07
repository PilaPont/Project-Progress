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
    task_deliverables_total_weight = fields.Float(related='task_id.task_deliverables_total_weight')
    project_deliverables_total_weight = fields.Float(related='project_id.deliverables_total_weight')

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

    @api.depends('project_deliverables_total_weight', 'task_deliverables_total_weight', 'deliverables_weighting_method')
    def _compute_normal_weight(self):
        import logging

        within_task_deliverables = self.filtered(
            lambda d: d.deliverables_weighting_method == 'within_task')
        within_project_deliverables = self.filtered(
            lambda d: d.deliverables_weighting_method == 'within_project')
        logging.critical('within_task_deliverables = {}'.format(within_task_deliverables))
        logging.critical('within_task_deliverables = {}'.format(within_task_deliverables))

        for deliverable in self.env['deliverable.item'].search(
                [('task_id', 'in', within_task_deliverables.mapped('task_id').ids)]):
            if deliverable.task_deliverables_total_weight == 0:
                deliverable.normal_weight = 0
            else:
                deliverable.normal_weight = deliverable.weight / deliverable.task_deliverables_total_weight if \
                    deliverable.task_deliverables_total_weight else 0
        for deliverable in self.env['deliverable.item'].search(
                [('project_id', 'in', within_project_deliverables.mapped('project_id').ids)]):
            logging.critical(
                'deli.project_deliverables_total_weight ={}, {}'.format(deliverable.weight,
                                                                        deliverable.project_deliverables_total_weight))
            if deliverable.project_deliverables_total_weight == 0:
                deliverable.normal_weight = 0
            else:
                deliverable.normal_weight = deliverable.weight / deliverable.project_deliverables_total_weight if \
                    deliverable.project_deliverables_total_weight else 0
