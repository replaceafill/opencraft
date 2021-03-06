# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Admin for the instance app
"""

# Imports #####################################################################

from django.contrib import admin

from instance.models.database_server import MySQLServer, MongoDBServer
from instance.models.instance import InstanceReference
from instance.models.load_balancer import LoadBalancingServer
from instance.models.log_entry import LogEntry
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.server import OpenStackServer


# ModelAdmins #################################################################

class LogEntryAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('created', 'level', 'text', 'modified')


class OpenStackServerAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('openstack_id', 'status', 'created', 'modified')
    # TODO: Is there a way to link back to the owning AppServer? (efficiently)


class InstanceReferenceAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('id', 'instance', 'created', 'modified')


class OpenEdXInstanceAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('internal_lms_domain', 'name', 'created', 'modified')


class OpenEdXAppServerAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('id', 'owner', 'name', 'created', 'modified')

    # Don't allow modifying an AppServer once created:
    readonly_fields = [field.name for field in OpenEdXAppServer._meta.get_fields(include_parents=True)]


class MySQLServerAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('name', 'description', 'hostname', 'port', 'username', 'password')


class MongoDBServerAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('name', 'description', 'hostname', 'port', 'username', 'password')


class LoadBalancingServerAdmin(admin.ModelAdmin): # pylint: disable=missing-docstring
    list_display = ('domain', 'ssh_username')


admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(OpenStackServer, OpenStackServerAdmin)
admin.site.register(InstanceReference, InstanceReferenceAdmin)
admin.site.register(OpenEdXInstance, OpenEdXInstanceAdmin)
admin.site.register(OpenEdXAppServer, OpenEdXAppServerAdmin)
admin.site.register(MySQLServer, MySQLServerAdmin)
admin.site.register(MongoDBServer, MongoDBServerAdmin)
admin.site.register(LoadBalancingServer, LoadBalancingServerAdmin)
