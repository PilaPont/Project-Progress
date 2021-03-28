{
    'name': 'Project Progress',
    'version': '14.0.0.0.1.0+210328',
    'summary': 'to measure project process base on different methods',
    'author': 'Kenevist Developers, Maryam Kia',
    'website': "www.kenevist.ir",
    'license': 'OPL-1',
    'category': 'Project',

    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'views/project_task_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
