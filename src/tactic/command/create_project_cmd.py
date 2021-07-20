###########################################################
#
# Copyright (c) 2005, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
# Description: Actions executed when an element of an EditWdg is called to
# update an sobject.  

__all__ = ['CreateProjectCmd']


import subprocess
import os, shutil, string, types, re, zipfile

from pyasm.common import Environment, System, TacticException, Config, Common
from pyasm.search import Search, SearchType, DatabaseImpl, DbContainer
from pyasm.command import Command
from pyasm.biz import Project, IconCreator


__all__.append("CopyFileToAssetTempCmd")
class CopyFileToAssetTempCmd(Command):
    def execute(self):
        filename = self.kwargs.get("filename")
        ticket = self.kwargs.get("ticket")
        upload_dir = Environment.get_upload_dir(ticket=ticket)
        # can't rely on that
        #ticket = Environment.get_ticket()
        asset_temp_dir = "%s/temp/%s" % (Environment.get_asset_dir(), ticket)

        if not os.path.exists(asset_temp_dir):
            os.makedirs(asset_temp_dir)

        from_path = "%s/%s" % (upload_dir, filename)
        icon_creator = IconCreator(from_path)
        icon_creator.execute()
        icon_path = icon_creator.get_icon_path()

        to_path = "%s/%s" % (asset_temp_dir, filename)
        
        if icon_path:
            shutil.copy(icon_path, to_path)
            self.info = {
                "web_path": "/assets/temp/%s/%s" % (ticket, filename),
                "lib_path": to_path
            }
        else:
            self.info = {}

        
class CreateProjectCmd(Command):

    def is_undoable(cls):
        return False
    is_undoable = classmethod(is_undoable)




    def get_title(self):
        return "Create Project"

    def get_args_keys(self):
        return {
        'project_code': 'code of the new project',
        'project_title': 'title of the new project',
        'project_type': 'determines the type of project which specifies the initial schema and the naming conventions',
        #'copy_pipelines': 'flag to copy template site pipelines to project'
        }

    def check(self):
        project_code = self.kwargs.get('project_code')
        regexs = '^\d|\W'
        m = re.search(r'%s' % regexs, project_code) 
        if m:
            if isinstance(project_code, unicode):
                project_code = project_code.encode('utf-8')
            else:
                project_code = unicode(project_code).encode('utf-8')
            raise TacticException('<project_code> [%s] cannot contain special characters or start with a number.' %project_code)

        # check to see if this project already exists
        test_project = Project.get_by_code(project_code)
        if test_project:
            if test_project.get_value('s_status') == 'retired':
                raise TacticException('Project with code [%s] already exists but is retired.' %project_code)
            else:
                raise TacticException('Project with code [%s] already exists.' %project_code)

        return True

    def execute(self):

        project_code = self.kwargs.get('project_code')
        project_title = self.kwargs.get('project_title')
        project_type = self.kwargs.get('project_type')
        project_description = self.kwargs.get("description")
        if not project_type:
            project_type = "simple"

        is_template = self.kwargs.get('is_template')
        project_theme = self.kwargs.get('project_theme')

        use_default_side_bar = self.kwargs.get('use_default_side_bar')
        if use_default_side_bar in [False, 'false']:
            use_default_side_bar = False
        else:
            use_default_side_bar = True


        assert project_code
        assert project_type
        if project_type:
            # check to see if it exists
            search = Search("sthpw/project_type")
            search.add_filter("code", project_type)
            project_type_sobj = search.get_sobject()
            if not project_type_sobj:

                # just create a default one in this case if it is named
                # after the project code
                if not is_template and project_type == project_code:
                    project_type = 'default'
                    
                # create a new project type
                search = Search("sthpw/project_type")
                search.add_filter("code", project_type)
                project_type_sobj = search.get_sobject()
                if not project_type_sobj:
                    project_type_sobj = SearchType.create("sthpw/project_type")
                    project_type_sobj.set_value("code", project_type)
                    project_type_sobj.set_value("type", "simple")

                    project_type_sobj.commit()

        # set the current project to Admin
        Project.set_project("admin")


        # create a new project sobject
        project = SearchType.create("sthpw/project")
        project.set_value("code", project_code)
        project.set_value("title", project_title)
        project.set_value("type", project_type)
        if project_description:
            project.set_value("description", project_description)
        # set the update of the database to current (this is obsolete)
        #project.set_value("last_db_update", "now()")
        project.set_value("last_version_update", "2.5.0.v01")

        if is_template in ['true', True, 'True']:
            project.set_value("is_template", True)
        else:
            project.set_value("is_template", False)


        if project_type != "default":
            category = Common.get_display_title(project_type)
            project.set_value("category", category)


        project.commit()
       
 

        # if there is an image, check it in
        upload_path = self.kwargs.get("project_image_path")
        if upload_path:
            if not os.path.exists(upload_path):
                raise TacticException("Cannot find upload image for project [%s]" % upload_path)
            file_type = 'main'

            file_paths = [upload_path]
            file_types = [file_type]

            source_paths = [upload_path]
            from pyasm.biz import IconCreator
            if os.path.isfile(upload_path):
                icon_creator = IconCreator(upload_path)
                icon_creator.execute()

                web_path = icon_creator.get_web_path()
                icon_path = icon_creator.get_icon_path()
                if web_path:
                    file_paths = [upload_path, web_path, icon_path]
                    file_types = [file_type, 'web', 'icon']

            from pyasm.checkin import FileCheckin
            checkin = FileCheckin(project, context='icon', file_paths=file_paths, file_types=file_types)
            checkin.execute()

        # find project's base_type
        base_type = project.get_base_type()

        if not base_type and project_type =='unittest':
            base_type = 'unittest'
        elif not base_type:
            base_type = 'simple'


        # get the database for this project
        db_resource = project.get_project_db_resource()

        database = db_resource.get_database_impl()
        #database = DatabaseImpl.get()
        database_type = database.get_database_type()
        if database_type == 'Oracle':
            raise TacticException("Creation of project is not supported. Please create manually")




        # creating project database
        print("Creating database '%s' ..." % project_code)
        try:
            # create the datbase
            database.create_database(db_resource)
        except Exception as e:
            print(str(e))
            print("WARNING: Error creating database [%s]" % project_code)





        # import the appropriate schema with config first
        database.import_schema(db_resource, base_type)

        self.create_schema(project_code)

        # before we upgrade, we have to commit the transaction
        # This is because upgrade actually run as separate processes
        # so if not commit has been made, the tables from importing the
        # schema will not have existed yet
        DbContainer.commit_thread_sql()


        self.upgrade()

        # import the appropriate data
        database.import_default_data(db_resource, base_type)


        # import default links
        if use_default_side_bar:
            self.import_default_side_bar()


        # create specified stypes
        self.create_search_types()


        # create theme
        if project_theme:
            self.create_theme(project_theme)



        # set as main project
        is_main_project = self.kwargs.get("is_main_project")
        if is_main_project in [True,'true','on']:
            Config.set_value("install", "default_project", project_code)
            Config.save_config()
            Config.reload_config()

        # initiate the DbContainer
        DbContainer.get('sthpw')


        self.info['result'] = "Finished creating project [%s]."%project_code

        print("Done.")



    def create_schema(self, project_code):
        # This may not be necessary
        return

        # create an empty schema
        schema = SearchType.create("sthpw/schema")
        schema.set_value("schema", "<schema/>")
        schema.set_value("code", project_code)
        schema.commit()




    def import_default_side_bar(self):
        code = Search.eval("@GET(config/widget_config['code','WIDGET_CONFIG000000'].code)", single=True)
        if code:
            print("Default side bar already exists!")
            return

        
        project_code = self.kwargs.get('project_code')
        # It looks like project=XXX on SearchType.create does not work
        Project.set_project(project_code)
        config = SearchType.create("config/widget_config?project=%s" % project_code)
        config.set_value("code", "WIDGET_CONFIG000000")
        config.set_value("category", "SideBarWdg")
        config.set_value("search_type", "SideBarWdg")
        config.set_value("view", "project_view")
        
        xml = '''<?xml version='1.0' encoding='UTF-8'?>
<config>
  <project_view>
    <element name='_home' title='Examples'/>
  </project_view>
</config>
'''
        config.set_value("config", xml)

        config.commit()



    def upgrade(self):
        project_code = self.kwargs.get('project_code')
        # run the upgrade script (this has to be done in a separate
        # process due to possible sql errors in a transaction
        install_dir = Environment.get_install_dir()
        python = Config.get_value("services", "python")
        if not python:
            python = "python"

        impl = Project.get_database_impl()

        from pyasm.search.upgrade import Upgrade
        version = Environment.get_release_version()
        version.replace('.', '_')
        upgrade = Upgrade(version, is_forced=True, project_code=project_code, quiet=True)
        upgrade.execute()



    def create_search_types(self):
        from tactic.ui.app import SearchTypeCreatorCmd

        project_code = self.kwargs.get('project_code')

        search_types = self.kwargs.get('project_stype')
        if not search_types:
            return

        for search_type in search_types:
            if search_type == "":
                continue

            search_type = Common.get_filesystem_name(search_type)

            if search_type.find("/") != -1:
                parts = search_type.split("/")
                namespace = parts[0]
                table = parts[1]
            else:
                namespace = project_code
                table = search_type

            search_type = "%s/%s" % (namespace, search_type)

            description = Common.get_display_name(table)
            title = description
            has_pipeline = True


            kwargs = {
                'database': project_code,
                'namespace': project_code,
                'schema': 'public',

                'search_type_name': search_type,
                'asset_description': description,
                'asset_title': title,
                'sobject_pipeline': has_pipeline,
            }

            creator = SearchTypeCreatorCmd(**kwargs)
            creator.execute()


    def create_theme(self, theme):

        # get a built-in plugin
        plugin_base_dir = Environment.get_plugin_dir()
        zip_path = "%s/%s.zip" % (plugin_base_dir, theme)
        manifest_path = "%s/%s/manifest.xml" % (plugin_base_dir, theme)

        plugin_base_dir2 = Environment.get_builtin_plugin_dir()
        zip_path2 = "%s/%s.zip" % (plugin_base_dir2, theme)
        manifest_path2 = "%s/%s/manifest.xml" % (plugin_base_dir2, theme)

        # install the theme
        from tactic.command import PluginInstaller
        if os.path.exists(manifest_path):
            plugin_dir = "%s/%s" % (plugin_base_dir, theme)
            installer = PluginInstaller(
                plugin_dir = plugin_dir,
                register=True
            )
            installer.execute()
            is_builtin = False
        elif os.path.exists(zip_path):
            installer = PluginInstaller(
                zip_path=zip_path,
                register=True
            )
            installer.execute()
            is_builtin = False
        elif os.path.exists(manifest_path2):
            plugin_dir = "%s/%s" % (plugin_base_dir2, theme)
            installer = PluginInstaller(
                plugin_dir = plugin_dir,
                register=True
            )
            installer.execute()
            is_builtin = True
        elif os.path.exists(zip_path2):
            installer = PluginInstaller(
                zip_path=zip_path2,
                register=True
            )
            installer.execute()
            is_builtin = True
        else: 
            raise Exception("Installation error: cannot find %s theme" % theme)

        from pyasm.biz import PluginUtil
        if is_builtin:
            plugin_util = PluginUtil(base_dir=plugin_base_dir2)
        else:
            plugin_util = PluginUtil()
        data = plugin_util.get_plugin_data(theme)

        # if the theme does not have the url defined (which it likely
        # shouldn't, but just in case ...
        search = Search("config/url")
        search.add_filter("url", "/index")
        url = search.get_sobject()
        if not url:

            index_view = data.get("index_view")
            if not index_view:
                # don't use the folder in the theme
                base = os.path.basename(theme)
                index_view = "%s/index" % base
            

            # set this as the default index
            search = SearchType.create("config/url")
            search.set_value("url", "/index")
            search.set_value("widget", '''
<element name='index'>
  <display class='tactic.ui.panel.CustomLayoutWdg'>
    <view>%s</view>
  </display>
</element>
            ''' % index_view )
            search.set_value("description", "Index Page")
            search.commit();







class CopyProjectFromTemplateCmd(Command):

    def execute(self):
        project_code = self.kwargs.get("project_code")
        template_code = self.kwargs.get("template_code")
        project_title = self.kwargs.get("project_title")

        # check to see if the template actually exists


        from tactic.command import ProjectTemplateInstallerCmd
        cmd = ProjectTemplateInstallerCmd(**self.kwargs)
        cmd.execute()





