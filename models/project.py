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
