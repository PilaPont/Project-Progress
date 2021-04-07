from odoo import api, fields, models, exceptions, _


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
    deliverables_total_weight = fields.Float(compute='_compute_deliverables_total_weight', store=True)
    tasks_total_weight = fields.Float(compute='_compute_tasks_total_weight', store=True)

    @api.constrains('use_deliverables')
    def _check_use_deliverables(self):
        if self.filtered(lambda item: item.deliverable_item_ids):
            raise exceptions.ValidationError(_('There are already deliverable items in this project.'))

    @api.depends('task_ids', 'task_ids.task_normal_weight', 'task_ids.task_progress')
    def _compute_project_progress(self):
        tasks = self.env['project.task'].search([('project_id', 'in', self.ids), ('child_ids', '=', False)])
        for project in self:
            project_tasks = tasks.filtered(lambda t: t.project_id == project)
            import logging
            logging.critical(
                'tasks = {} /n {} /n{}'.format(project_tasks.mapped('name'), project_tasks.mapped('task_normal_weight'),
                                               project_tasks.mapped('task_progress')))
            project.project_progress = sum(task.task_progress * task.task_normal_weight for task in project_tasks)

    @api.depends('deliverables_weighting_method', 'deliverable_item_ids.weight')
    def _compute_deliverables_total_weight(self):
        import logging
        for project in self.filtered(lambda p: p.deliverables_weighting_method == 'within_project'):
            logging.critical('project total delis = {}'.format(sum(project.deliverable_item_ids.mapped('weight'))))
            project.deliverables_total_weight = sum(project.deliverable_item_ids.mapped('weight'))

    @api.depends('task_ids.task_weight')
    def _compute_tasks_total_weight(self):
        tasks = self.env['project.task'].search([('project_id', 'in', self.ids), ('child_ids', '=', False)])
        for project in self:
            project_tasks = tasks.filtered(lambda t: t.project_id == project)
            project.tasks_total_weight = sum(project_tasks.mapped('task_weight'))
            import logging
            logging.critical('project total weight = {} , {}'.format(project.name, project.tasks_total_weight))

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
            import logging
            logging.critical('task_name , subtasks_name = {}, {}'.format(task.name, task.child_ids.mapped('name')))
            logging.critical('task_progress , subtasks_progress = {}, {}, {}'.format(task.task_progress,
                                                                                     task.child_ids.mapped(
                                                                                         'task_progress'),
                                                                                     task.task_weight))
            task.subtask_progress = sum(
                subtask.task_progress * subtask.task_weight / task.task_weight if task.task_weight else 0 for subtask in
                task.child_ids)

    @api.depends('subtask_progress', 'deliverable_progress', 'is_closed')
    def _compute_task_progress(self):
        import logging
        for task in self:
            if task.is_closed:
                task.task_progress = 100
                logging.critical('task_pro = {}'.format(task.task_progress))
            elif task.child_ids:
                logging.critical('task_childs = {}'.format(task.child_ids))

                task.task_progress = task.subtask_progress
            elif task.deliverable_item_ids:
                task.task_progress = task.deliverable_progress
            else:
                task.task_progress = 0

    @api.depends('task_weighting', 'automatic_task_weighting', 'child_ids', 'child_ids.task_weight')
    def _compute_task_weight(self):
        self.filtered(lambda rec: rec.active and not rec.task_weighting).write({'task_weight': 1})
        for task in self.filtered(lambda rec: rec.task_weighting and rec.subtask_count):
            task.task_weight = sum(task.child_ids.filtered(lambda children: children.active).mapped('task_weight'))
        for task in self.filtered(lambda rec: rec.task_weighting and rec.automatic_task_weighting):
            task.task_weight = sum(task.mapped('deliverable_item_ids.weight'))

    @api.depends('deliverable_item_ids.weight')
    def _compute_task_deliverables_total_weight(self):
        for task in self:
            task.task_deliverables_total_weight = sum(task.deliverable_item_ids.mapped('weight'))

    @api.depends('project_total_task_weight')
    def _compute_task_normal_weight(self):
        for task in self:
            task.task_normal_weight = task.task_weight / task.project_total_task_weight if \
                task.project_total_task_weight else 0

    task_weight = fields.Float(compute='_compute_task_weight', store=True)
    task_deliverables_total_weight = fields.Float(compute='_compute_task_deliverables_total_weight', store=True)
    project_total_task_weight = fields.Float(related='project_id.tasks_total_weight')
    task_normal_weight = fields.Float(compute='_compute_task_normal_weight', store=True)
    task_progress = fields.Float(string='Progress', compute='_compute_task_progress', store=True, default=0)
    subtask_progress = fields.Float(compute='_compute_subtask_progress', store=True)
    deliverable_progress = fields.Float(compute='compute_deliverables_stats', string='Progress', store=True)
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
