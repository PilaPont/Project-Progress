from odoo import api, fields, models


class Project(models.Model):
    _inherit = "project.project"
    _description = "Project"

    use_deliverables = fields.Boolean()
    use_deliverables_weighting = fields.Boolean()
    deliverables_weighting_method = fields.Selection([
        ('within_task', 'Within Task'),
        ('within_project', 'Within Project'),
    ])
    task_weighting = fields.Boolean()
    automatic_task_weighting = fields.Boolean(help='based on deliverable items weighting')
    project_progress = fields.Integer(compute='_compute_project_progress', store=True)

    @api.depends('task_ids', 'task_ids.is_closed')
    def _compute_project_progress(self):
        tasks = self.env['project.task'].search([('project_id', 'in', self.ids)])

        for project in self:
            if not project.use_deliverables:
                project_tasks = tasks.filtered(lambda t: t.project_id == project)
                total_tasks_count = len(project_tasks)
                done_tasks_count = len(project_tasks.filtered(lambda t: t.is_closed))
                project.project_progress = done_tasks_count / total_tasks_count * 100


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

    @api.depends()
    def _compute_task_progress(self):
        pass

    @api.depends('task_weighting')
    def _compute_task_weight(self):
        for task in self:
            if not task.task_weighting:
                task.task_weight = 1

    task_weight = fields.Integer(compute='_compute_task_weight', store=True)
    task_progress = fields.Integer(compute='_compute_task_progress', store=True)
    deliverable_item_ids = fields.One2many('deliverable.item', 'task_id', string='Check List')
    deliverables_progress = fields.Float(compute='compute_deliverables_stats', string='Weighted progress', store=True)
    deliverable_items_count = fields.Integer(compute='compute_deliverables_stats', string='Total Deliverable Items',
                                             store=True)
    done_deliverable_items_count = fields.Integer(compute='compute_deliverables_stats', string='Done Deliverable Items',
                                                  store=True)
    use_deliverables = fields.Boolean(related='project_id.use_deliverables')
    task_weighting = fields.Boolean(related='project_id.task_weighting')
