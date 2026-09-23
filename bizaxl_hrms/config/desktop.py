# -*- coding: utf-8 -*-

from frappe import _


def get_data():
    return [
        {
            "module_name": "Bizaxl HR",
            "type": "module",
            "label": _("Bizaxl HR"),
            "color": "#1F3B4D",
            "icon": "octicon octicon-people",
            "hidden": 0,
            "link": "List/Portal Task",
        },
        {
            "module_name": "Bizaxl HR",
            "category": "Modules",
        },
    ]