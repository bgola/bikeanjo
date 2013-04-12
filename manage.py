#!/usr/bin/env python
import os, sys

sys.path.insert(0, os.path.abspath(
                os.path.join(os.path.abspath(os.path.dirname(__file__)),
                os.pardir, os.pardir)))
sys.path.insert(0,
                os.path.abspath(
                os.path.join(os.path.abspath(os.path.dirname(__file__)),
                os.pardir)))
sys.path.insert(0,
                os.path.abspath(
                os.path.abspath(os.path.dirname(__file__))))

sys.path.insert(0,
                os.path.abspath(
                os.path.join(os.path.abspath(os.path.dirname(__file__)), 'chris')))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chris.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
