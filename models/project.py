from odoo import api, fields, models


class Project(models.Model):
    _inherit = "project.project"
    _description = "Project"

    use_deliverables = fields.Boolean()
    use_deliverables_weighting = fields.Boolean()
    deliverables_weighting_method = fields.Selection([
        ('within_task', 'Within Task'),
        ('within_project', 'Within Project')],
        default='within_task')
    task_weighting = fields.Boolean()
    automatic_task_weighting = fields.Boolean(help='based on deliverable items weighting')
    project_progress = fields.Float(compute='_compute_project_progress', store=True)
    deliverable_item_ids = fields.One2many(comodel_name='deliverable.item', inverse_name='project_id',
                                           string='Deliverable Items')

    @api.depends('task_ids', 'task_ids.task_normal_weight', 'task_ids.task_progress')
    def _compute_project_progress(self):
        tasks = self.env['project.task'].search([('project_id', 'in', self.ids)])
        for project in self:
            project_tasks = tasks.filtered(lambda t: t.project_id == project)
            project.project_progress = sum(task.task_progress * task.task_normal_weight for task in project_tasks)

    @api.onchange('use_deliverables')
    def _onchange_use_deliverables(self):
        if not self.use_deliverables:
            self.use_deliverables_weighting = False

    @api.onchange('use_deliverables_weighting')
    def _onchange_use_deliverables_weighting(self):
        if not self.use_deliverables_weighting:
            self.deliverables_weighting_method = 'within_task'

    @api.onchange('deliverables_weighting_method')
    def _onchange_deliverables_weighting_method(self):
        if self.deliverables_weighting_method == 'within_task':
            self.automatic_task_weighting = False


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.depends('deliverable_item_ids', 'deliverable_item_ids.done', 'deliverable_item_ids.weight')
    def compute_deliverables_stats(self):
        """:return the value for the deliverable items progress"""
        for task in self:
            total_items = task.deliverable_item_ids
            done_items = task.deliverable_item_ids.filtered('done')
            total_weight = sum(total_items.mapped('weight'))
            if total_weight:  # constrains are checked at create time so it is possible to have zero weight at run time
                task.deliverable_progress = sum(done_items.mapped('weight')) / total_weight * 100
            task.deliverable_items_count = len(total_items)
            task.done_deliverable_items_count = len(done_items)

    @api.depends('child_ids', 'child_ids.task_normal_weight', 'child_ids.task_progress', 'child_ids.is_closed')
    def _compute_subtask_progress(self):
        for task in self:
            task.subtask_progress = sum(
                subtask.task_progress * subtask.task_normal_weight for subtask in task.child_ids) * 100

    @api.depends('subtask_progress', 'deliverable_progress', 'is_closed')
    def _compute_task_progress(self):
        for task in self:
            if task.is_closed:
                task.task_progress = 100
            elif task.child_ids:
                task.task_progress = task.subtask_progress
            elif task.deliverable_item_ids:
                task.task_progress = task.deliverable_progress

    @api.depends('task_weighting', 'automatic_task_weighting')
    def _compute_task_weight(self):
        projects_sum_deliverable_weight = self.env['deliverable.item'].read_group(
            [('project_id', 'in', self.mapped('project_id.id'))],
            ['project_id', 'weight:sum(weight)'],
            groupby=['project_id'])
        projects_sum_deliverable_weight_dict = dict()
        for item in projects_sum_deliverable_weight:
            projects_sum_deliverable_weight_dict[item['project_id'][0]] = item['weight']
        for task in self:
            if not task.task_weighting:
                task.task_weight = 1
            elif task.task_weight and task.automatic_task_weighting:
                task.task_weight = sum(task.mapped('deliverable_item_ids.weight')) / \
                                   projects_sum_deliverable_weight_dict[
                                       task.project_id.id]

    @api.depends('task_weight')
    def _compute_task_normal_weight(self):
        projects_sum_task_weight = self.read_group([('project_id', 'in', self.mapped('project_id.id'))],
                                                   ['project_id', 'task_weight:sum(task_weight)'],
                                                   groupby=['project_id'])
        projects_sum_task_weight_dict = dict()
        for item in projects_sum_task_weight:
            projects_sum_task_weight_dict[item['project_id'][0]] = item['task_weight']
        for task in self:
            task.task_normal_weight = task.task_weight / projects_sum_task_weight_dict[task.project_id.id]

    task_weight = fields.Float(compute='_compute_task_weight', store=True)
    task_normal_weight = fields.Float(compute='_compute_task_normal_weight', store=True)
    task_progress = fields.Float(compute='_compute_task_progress', store=True, default=0)
    subtask_progress = fields.Float(compute='_compute_subtask_progress', store=True)
    deliverable_progress = fields.Float(compute='compute_deliverables_stats', string='Weighted progress', store=True)
    deliverable_item_ids = fields.One2many(comodel_name='deliverable.item', inverse_name='task_id',
                                           string='Deliverable Items')
    deliverable_items_count = fields.Integer(compute='compute_deliverables_stats', string='Total Deliverable Items',
                                             store=True)
    done_deliverable_items_count = fields.Integer(compute='compute_deliverables_stats', string='Done Deliverable Items',
                                                  store=True)
    use_deliverables = fields.Boolean(related='project_id.use_deliverables')
    task_weighting = fields.Boolean(related='project_id.task_weighting')
    automatic_task_weighting = fields.Boolean(related='project_id.automatic_task_weighting')
    deliverables_weighting_method = fields.Selection(related='project_id.deliverables_weighting_method')
