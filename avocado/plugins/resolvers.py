# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: Red Hat Inc. 2019
# Authors: Cleber Rosa <crosa@redhat.com>

"""
Test resolver for builtin test types
"""

import os

from avocado.core.plugin_interfaces import Resolver
from avocado.core.safeloader import find_avocado_tests
from avocado.core.safeloader import find_python_unittests
from avocado.core.resolver import ReferenceResolution
from avocado.core.resolver import ReferenceResolutionResult
from avocado.core.resolver import check_file
from avocado.core.nrunner import Runnable


class ExecTestResolver(Resolver):

    name = 'exec-test'
    description = 'Test resolver for executable files to be handled as tests'

    @staticmethod
    def resolve(reference):

        criteria_check = check_file(reference, reference, suffix=None,
                                    type_name='executable file',
                                    access_check=os.R_OK | os.X_OK,
                                    access_name='executable')
        if criteria_check is not True:
            return criteria_check

        return ReferenceResolution(reference,
                                   ReferenceResolutionResult.SUCCESS,
                                   [Runnable('exec-test', reference)])


class PythonUnittestResolver(Resolver):

    name = 'python-unittest'
    description = 'Test resolver for Python Unittests'

    @staticmethod
    def resolve(reference):

        criteria_check = check_file(reference, reference)
        if criteria_check is not True:
            return criteria_check

        class_methods = find_python_unittests(reference)
        if class_methods:
            runnables = []
            mod = os.path.relpath(reference)
            if mod.endswith('.py'):
                mod = mod[:-3]
            mod = mod.replace(os.path.sep, ".")
            for klass, meths in class_methods.items():
                for (meth, tags) in meths:
                    uri = '%s.%s.%s' % (mod, klass, meth)
                    runnables.append(Runnable('python-unittest',
                                              uri=uri,
                                              tags=tags))
            if runnables:
                return ReferenceResolution(reference,
                                           ReferenceResolutionResult.SUCCESS,
                                           runnables)

        return ReferenceResolution(reference,
                                   ReferenceResolutionResult.NOTFOUND)


class AvocadoInstrumentedResolver(Resolver):

    name = 'avocado-instrumented'
    description = 'Test resolver for Avocado Instrumented tests'

    @staticmethod
    def resolve(reference):
        if ':' in reference:
            module_path, _ = reference.split(':', 1)
        else:
            module_path = reference

        criteria_check = check_file(module_path, reference)
        if criteria_check is not True:
            return criteria_check

        # disabled tests not needed here
        class_methods_info, _ = find_avocado_tests(module_path)
        runnables = []
        for klass, methods_tags in class_methods_info.items():
            for (method, tags) in methods_tags:
                uri = "%s:%s.%s" % (module_path, klass, method)
                runnables.append(Runnable('avocado-instrumented',
                                          uri=uri,
                                          tags=tags))
        if runnables:
            return ReferenceResolution(reference,
                                       ReferenceResolutionResult.SUCCESS,
                                       runnables)

        return ReferenceResolution(reference,
                                   ReferenceResolutionResult.NOTFOUND)
