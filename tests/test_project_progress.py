from odoo.tests.common import SavepointCase, tagged


@tagged('-at_install', 'post_install')
class TestProjectProgressCommon(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestProjectProgressCommon, cls).setUpClass()

        # partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

        # project and tasks
        cls.test_project = cls.env['project.project'].create({
            'name': 'Test Project',
        })

        cls.new_state = cls.env['project.task.type'].create({
            'name': 'New',
            'sequence': 1,
            'project_ids': [(4, cls.test_project.id)],
        })

        cls.done_state = cls.env['project.task.type'].create({
            'name': 'Done',
            'sequence': 2,
            'project_ids': [(4, cls.test_project.id)],
            'is_closed': True
        })

        cls.task_1 = cls.env['project.task'].create({
            'name': 'Task 1',
            'project_id': cls.test_project.id,
        })

        cls.task_2 = cls.env['project.task'].create({
            'name': 'Task 2',
            'project_id': cls.test_project.id,
        })
        cls.task_3 = cls.env['project.task'].create({
            'name': 'Task 3',
            'project_id': cls.test_project.id,
        })

        cls.task_4 = cls.env['project.task'].create({
            'name': 'Task 4',
            'project_id': cls.test_project.id,
            'stage_id': cls.done_state.id
        })

    def test_without_deliverables(self):
        """Nothing has been checked yet. we just have four tasks
         without deliverables and subtasks.
        """
        import logging
        logging.critical('progress tasks  {}, {}, {}, {}'.format(self.task_1.task_progress, self.task_2.task_progress,
                                                                 self.task_3.task_progress, self.task_4.task_progress))
        logging.critical('task 4 close  {}'.format(self.task_4.is_closed))
        logging.critical('task 4 close  {}'.format(self.task_4.stage_id.is_closed))

        self.assertEqual(self.test_project.project_progress, ((0 + 0 + 0 + 100) / 4),
                         'project progress was not calculated correctly.')

