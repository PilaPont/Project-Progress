from odoo.tests.common import SavepointCase, tagged
from odoo.tools import float_compare


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
            'allow_subtasks': True
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


@tagged('-at_install', 'post_install')
class TestProjectProgressCommonSubtasks(TestProjectProgressCommon):

    @classmethod
    def setUpClass(cls):
        super(TestProjectProgressCommonSubtasks, cls).setUpClass()

        cls.task_1_1 = cls.env['project.task'].create({
            'name': 'Child Task 1_1',
            'parent_id': cls.task_1.id,
        })
        cls.task_1_2 = cls.env['project.task'].create({
            'name': 'Child Task 1_2',
            'parent_id': cls.task_1.id,
            'stage_id': cls.done_state.id
        })
        cls.task_1_3 = cls.env['project.task'].create({
            'name': 'Child Task 1_3',
            'parent_id': cls.task_1.id,
        })
        cls.task_1_3_1 = cls.env['project.task'].create({
            'name': 'Child Task 1_3_1',
            'parent_id': cls.task_1_3.id,
        })
        cls.task_1_3_2 = cls.env['project.task'].create({
            'name': 'Child Task 1_3_2',
            'parent_id': cls.task_1_3.id,
        })


@tagged('-at_install', 'post_install')
class TestProjectProgressCommonTasksWaiting(TestProjectProgressCommonSubtasks):

    @classmethod
    def setUpClass(cls):
        super(TestProjectProgressCommonTasksWaiting, cls).setUpClass()
        cls.test_project.task_weighting = True
        cls.task_1_3_2.stage_id = cls.done_state
        cls.task_2.task_weight = 20
        cls.task_3.task_weight = 20
        cls.task_1_2.task_weight = 2
        cls.task_1_3_1.task_weight = 40
        cls.task_1_3_2.task_weight = 30


@tagged('-at_install', 'post_install')
class TestProjectProgressCommonDeliverables(TestProjectProgressCommonSubtasks):

    @classmethod
    def setUpClass(cls):
        super(TestProjectProgressCommonDeliverables, cls).setUpClass()

        cls.test_project.use_deliverables = True

        cls.deliverable_1_3_1_d1 = cls.env['deliverable.item'].create({
            'name': 'T1_3_1 D1',
            'task_id': cls.task_1_3_1.id,
            'done': True,
        })
        cls.deliverable_1_3_1_d2 = cls.env['deliverable.item'].create({
            'name': 'T1_3_1 D2',
            'task_id': cls.task_1_3_1.id,
        })
        cls.deliverable_3_1 = cls.env['deliverable.item'].create({
            'name': 'T3 D1',
            'task_id': cls.task_3.id,
        })


@tagged('-at_install', 'post_install')
class TestProjectProgressCommonDeliverablesWaiting(TestProjectProgressCommonDeliverables):

    @classmethod
    def setUpClass(cls):
        super(TestProjectProgressCommonDeliverablesWaiting, cls).setUpClass()
        cls.test_project.use_deliverables_weighting = True
        cls.deliverable_1_3_1_d1.weight = 60
        cls.deliverable_1_3_1_d2.weight = 50
        cls.deliverable_3_1.weight = 70


@tagged('-at_install', 'post_install')
class TestWithoutDeliverables(TestProjectProgressCommon):
    # case 1
    def test_without_deliverables(self):
        """Nothing has been checked yet. we just have four tasks
         without deliverables and subtasks.
        """
        self.assertEqual(float_compare(self.test_project.project_progress, 25, 0), 0)


@tagged('-at_install', 'post_install')
class TestWithDeliverables(TestProjectProgressCommonDeliverables):
    # case 2
    def test_with_some_deliverables_done(self):
        self.assertEqual(float_compare(self.test_project.project_progress, 36, 0), 0)


@tagged('-at_install', 'post_install')
class TestWithTaskWaiting(TestProjectProgressCommonTasksWaiting):
    # case 3

    def test_with_task_waiting(self):
        self.assertEqual(float_compare(self.test_project.project_progress, 29, 0), 0)


@tagged('-at_install', 'post_install')
class TestWithTaskWaitingAndDeliverables(TestProjectProgressCommonTasksWaiting, TestProjectProgressCommonDeliverables):
    # case 4
    def test_with_task_waiting(self):
        total_normal_weight = sum(self.env['project.task'].search(
            [('project_id', '=', self.test_project.id), ('child_ids', '=', False)]).mapped(
            'task_normal_weight'))
        self.assertEqual(float_compare(total_normal_weight, 1, 0), 0)
        self.assertEqual(float_compare(self.test_project.project_progress, 46, 0), 0)


@tagged('-at_install', 'post_install')
class TestWithTaskWaitingAndDeliverablesWaiting(TestProjectProgressCommonTasksWaiting,
                                                TestProjectProgressCommonDeliverablesWaiting):
    # case 5
    def test_task_and_deliverables_waiting_task_base(self):
        self.assertEqual(float_compare(self.test_project.project_progress, 48, 0), 0)

    def test_task_and_deliverables_waiting_project_base(self):
        # case 6
        self.test_project.deliverables_weighting_method = 'within_project'
        self.assertEqual(float_compare(self.test_project.project_progress, 48, 0), 0)

        # case 7
        self.test_project.automatic_task_weighting = True
        self.assertEqual(float_compare(self.test_project.project_progress, 33, 0), 0)


@tagged('-at_install', 'post_install')
class TestWithDeliverablesWaiting(TestProjectProgressCommonDeliverablesWaiting):
    # case 8
    def test_deliverables_waiting_task_base(self):
        total_normal_weight = sum(self.env['project.task'].search(
            [('project_id', '=', self.test_project.id), ('child_ids', '=', False)]).mapped(
            'task_normal_weight'))
        self.assertEqual(float_compare(total_normal_weight, 1, 0), 0)
        self.assertEqual(float_compare(self.test_project.project_progress, 36, 0), 0)

    # case 9
    def test_deliverables_waiting_project_base(self):
        self.test_project.deliverables_weighting_method = 'within_project'
        self.assertEqual(float_compare(self.test_project.project_progress, 36, 0), 0)
