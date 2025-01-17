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

__all__ = ['ShelfWdg', 'ShelfEditWdg', 'ScriptEditorWdg']

from pyasm.common import Environment, Common, SecurityException, Container
from pyasm.biz import ProjectSetting
from pyasm.search import Search
from pyasm.web import DivWdg, HtmlElement, SpanWdg, Table, Widget, WebContainer
from pyasm.widget import TextAreaWdg, ButtonWdg, TextWdg, HiddenWdg, ProdIconButtonWdg, SelectWdg, IconWdg

from tactic.ui.common import BaseRefreshWdg
from tactic.ui.container import PopupWdg
from tactic.ui.widget import ActionButtonWdg, DirListWdg
from tactic.ui.input import TextInputWdg

import os

class ShelfWdg(BaseRefreshWdg):
    '''This is a shelf of clickable icons that execute custom javascript '''

    def get_args_keys(self):
        return {
        }


    def get_display(self):

        div = DivWdg()

        js_editor_wdg = ShelfEditWdg()

        # div.add( "[<span onclick='document.id(\"ShelfEditWdg\").setStyle(\"display\",\"block\");' style='cursor: pointer;'>" \
        #          "js_edit<span>]" )

        launch_link = DivWdg()
        launch_link.add( "[js_edit]" )
        launch_link.add_style("cursor: pointer;")
        launch_link.add_behavior( {
            "type": "click_up",
            "cbjs_action": "spt.popup.open('ShelfEditWdg', false);"
        } )

        div.add( launch_link )
        div.add( js_editor_wdg )

        return div




    def get_button_wdg(self, script_name):
        func_name = script_name

        custom_script = self.get_custom_script(script_name)


        script = HtmlElement.script('''
        %s = function() {
            %s
        }
        ''' % (func_name, custom_script) )


        button = SpanWdg()
        button.add_class("hand")
        button.add(script)
        button.add("[%s]" % script_name)
        button.add_event("onclick", "%s()" % func_name)

        return button


    def get_custom_script(self, script_name):


        if script_name == "first":
            custom_script = '''
            server = TacticServerStub.get();
            var ping = server.ping();
            alert(ping);
            '''
        elif script_name == "second":
            custom_script = '''
            refresh_widget("sample")
            '''
        elif script_name == "third":
            custom_script = '''
            var applet = spt.Applet.get();
            applet.exec("notepad");
            '''
        elif script_name == "js_edit":
            custom_script = '''
            document.id('ShelfEditWdg').setStyle("display", 'block');
            '''
        else:
            custom_script = "alert('[%s] not implemented')" % script_name

        return custom_script





class ScriptEditorWdg(BaseRefreshWdg):
    '''This is a simple editor for shelf custom code'''

    def init(self):
        
        self.search_type = "config/custom_script"
        security = Environment.get_security()
        if not security.check_access("builtin", "view_script_editor", "allow"):
            raise SecurityException('You are not allowed to access this widget.')

    def get_args_keys(self):
        return {
        'script_path': 'script path to open to'
        }


    def get_display(self):
        top = self.top
        top.add_class("spt_script_editor_top")

        """
        top.add_class("SPT_CHANGE")
        top.add_behavior( {
            'type': 'load',
            'cbjs_action': '''
            register_change = function(bvr) {
                var change_top = bvr.src_el.getParent(".SPT_CHANGE"); 
                change_top.addClass("SPT_HAS_CHANGES");
                change_top.update_change(change_top, bvr);
            }

            has_changes = function(bvr) {
                var change_top = bvr.src_el.getParent(".SPT_CHANGE"); 
                return change_top.hasClass("SPT_HAS_CHANGES");
            }

            bvr.src_el.update_change = function(top, bvr) {
                change_el = top.getElement(".spt_change_element");
                change_el.setStyle("display", "");
            }
            '''
        } )
        """

        change_div = DivWdg()
        top.add(change_div)
        #change_div.add("CHANGES!!!")
        change_div.add_style("display: none")
        change_div.add_class("spt_change_element")





        top.add_class("spt_panel")
        top.add_class("spt_js_editor")
        top.add_attr("spt_class_name", Common.get_full_class_name(self) )
        top.add_color("background", "background")
        top.add_style("padding", "10px")
       


        div = DivWdg()
        top.add(div)


        # if script_path
        script_path = self.kwargs.get("script_path")
        search_key = self.kwargs.get("search_key")
        if script_path:
            search = Search("config/custom_script")
            dirname = os.path.dirname(script_path)
            basename = os.path.basename(script_path)

            search.add_filter("folder", dirname)
            search.add_filter("title", basename)
            script_sobj = search.get_sobject()
        elif search_key:
            script_sobj = Search.get_by_search_key(search_key)
        else:
            script_sobj = None


        if script_sobj:
            script_code = script_sobj.get_value("code")
            script_folder = script_sobj.get_value("folder")
            script_name = script_sobj.get_value("title")
            script_value = script_sobj.get_value("script")
            script_language = script_sobj.get_value("language")
        else:
            script_code = ''
            script_folder = ''
            script_name = ''
            script_value = ''
            script_language = ''




        editor = AceEditorWdg(custom_script=script_sobj, language=script_language)
        self.editor_id = editor.get_editor_id()


        if not Container.get_dict("JSLibraries", "spt_script_editor"):
            div.add_behavior( {
                'type': 'load',
                'cbjs_action': self.get_onload_js()
            } )


        # create the insert button
        help_button_wdg = DivWdg()
        div.add(help_button_wdg)
        help_button_wdg.add_style("float: right")
        help_button = ActionButtonWdg(title="?", tip="Script Editor Help", size='s')
        help_button_wdg.add(help_button)

        help_button.add_behavior( {
            'type': 'click_up',
            'cbjs_action': '''spt.help.load_alias("tactic-script-editor")'''
        } )


        # create the insert button
        add_button_wdg = DivWdg()
        add_button_wdg.add_style("float: right")
        add_button = ActionButtonWdg(title="Manage")
        add_button.add_behavior( {
            'type': 'click_up',
            'cbfn_action': 'spt.popup.get_widget',
            'options': {
                'class_name': 'tactic.ui.panel.ViewPanelWdg',
                'title': 'Manage: [%s]' % self.search_type
            },
            'args': {
                'search_type': self.search_type,
                'view': 'table',
                'show_shelf': False,
                'element_names': ['folder', 'title', 'description', 'language'],
            },
        } )
        
        add_button_wdg.add(add_button)
        div.add(add_button_wdg)


        button_div = editor.get_buttons_wdg()
        div.add(button_div)
            
        """
        button_div = DivWdg()
        #div.add(button_div)

        button_div.add_style("text-align: left")

        button = ActionButtonWdg(title="Run")
        button.add_style("float: left")
        button.add_style("margin: 0 10 3")
        button.add_behavior( {
            'type': 'click_up',
            'cbjs_action': '''
            //var editor = document.id('shelf_script');
            var value = editAreaLoader.getValue('shelf_script')
            eval( value )
            '''
        } )
        button_div.add(button)


        button = ActionButtonWdg(title="Save")
        button.add_style("float: left")
        button.add_style("margin: 0 10 3")
        #button = ProdIconButtonWdg("Save")
        #button.add_style("margin: 5 10")
        behavior = {
            'type': 'click_up',
            'cbfn_action': 'spt.script_editor.save_script_cbk'
        }
        button.add_behavior(behavior)
        button_div.add(button)


        button = ActionButtonWdg(title="Clear")
        button.add_style("float: left")
        button.add_style("margin: 0 10 3")
        #button = ProdIconButtonWdg("Clear")
        #button.add_style("margin: 5 10")
        button.add_behavior( {
            'type': 'click_up',
            'cbjs_action': '''
            spt.api.Utility.clear_inputs( bvr.src_el.getParent('.spt_js_editor') );
            editAreaLoader.setValue('shelf_script', '');

            '''
        } )

        button_div.add(button)
        """

        div.add( "<br clear='all'/><br/>")

        save_wdg = DivWdg()
        save_wdg.add_class("spt_script_path")
        div.add(save_wdg)
        save_wdg.add_style("padding: 2px 5px 6px 5px")
        #save_wdg.add_color("background", "background", -5)


        # script code
        save_span = Table()
        save_wdg.add(save_span)
        save_span.add_row()

        code_span = SpanWdg()
        code_span.add("<b>Code: &nbsp;</b>")
        td = save_span.add_cell(code_span)
        td.add_style("display: none")
        code_text = TextInputWdg(name="shelf_code")
        code_text.add_style("display: inline")
        code_text.add_style("width: 100px")
        code_text.set_value(script_code)
        code_text.add_attr("readonly", "true")
        code_text.set_id("shelf_code")
        code_text.add_class("spt_code")
        td = save_span.add_cell(code_text)
        td.add_style("padding-top: 10px")

        td.add_style("display: none")


        save_span.add_cell("&nbsp;&nbsp;")

        # script name (path??)
        td = save_span.add_cell("<b>Script Path: &nbsp;</b>")
        td.add_style("padding-top: 10px")
        save_text = TextInputWdg(name="shelf_folder")
        save_text.add_style("width: 250px")
        save_text.set_id("shelf_folder")
        save_text.add_class("spt_folder")
        save_text.set_value(script_folder)
        td = save_span.add_cell(save_text)
        td.add_style("padding-top: 10px")

        td = save_span.add_cell("&nbsp; / &nbsp;")
        td.add_style("padding-top: 10px")
        td.add_style("font-size: 1.5em")
        save_text = TextInputWdg(name="shelf_title")
        save_text.add_style("width: 350px")
        save_text.add_attr("size", "40")
        save_text.set_id("shelf_title")
        save_text.add_class("spt_title")
        save_text.set_value(script_name)
        td = save_span.add_cell(save_text)
        td.add_style("padding-top: 10px")

        from tactic.ui.container import ResizableTableWdg
        table = ResizableTableWdg()
        table.add_row()

        td = table.add_cell(resize=False)
        td.add_style("vertical-align: top")

        td.add(editor)


        text = TextAreaWdg("shelf_script")



        td = table.add_cell()
        td.add_style('vertical-align: top')
        td.add(self.get_script_wdg())


        table.add_row(resize=False)


        div.add(table)

        if self.kwargs.get("is_refresh"):
            return div
        else:
            return top



    def get_script_wdg(self):

        search = Search("config/custom_script")
        #search.add_user_filter()
        search.add_order_by("folder")
        search.add_order_by("title")
        scripts = search.get_sobjects()

        widget = DivWdg()
        widget.add_style("width: 100%")

        from pyasm.web.palette import Palette
        palette = Palette.get()
        bg_color = palette.color("background3")
        hover_color = palette.color("background3", 20)
        widget.add_color("background", bg_color)


        title = DivWdg()
        title.add("Saved Scripts")
        title.add_style("font-size: 14px")
        title.add_color("color", "color")
        title.add_style("padding: 8px 3px")
        title.add_style("margin: 0 0 0 -1")
        title.add_color("background", "background", -5)
        title.add_border()
        widget.add(title)


        script_div = DivWdg()
        script_div.add_border()
        script_div.add_color("background", "background3")
        script_div.add_color("color", "color3")
        script_div.add_style("padding: 8px")
        script_div.add_style("overflow-x: hidden")
        script_div.add_style("overflow-y: auto")
        script_div.add_style("height: 100%")
        script_div.add_style("min-width: 100px")
        script_div.add_style("width: 220px")
        script_div.add_style("margin: -1px 0px 0px -1px")
        script_div.add_class("spt_resizable")

        inner = DivWdg()
        script_div.add(inner)
        inner.add_style("height: 100%")
        inner.add_style("width: 800px")


        paths = []
        scripts_dict = {}
        for script in scripts:
            path = "///%s/%s" % (script.get_value("folder"), script.get_value("title"))
            paths.append(path)
            scripts_dict[path] = script
        dir_list_wdg = ScriptDirListWdg(paths=paths, base_dir="/", editor_id=self.editor_id, scripts=scripts_dict)
        inner.add(dir_list_wdg)


        """
        last_folder = ''
        for script in scripts:
            title = script.get_value("title")
            folder = script.get_value("folder")
            language = script.get_value("language", no_exception=True)
            if not language:
                language = 'javascript'

            if folder != last_folder:
                div = DivWdg()
                icon = IconWdg("Script", IconWdg.FOLDER)
                div.add(icon)
                div.add(" %s" % folder)
                inner.add(div)


            last_folder = folder

            div = DivWdg()
            inner.add(div)
            div.add_class('hand')
            icon = IconWdg("Script", IconWdg.TOGGLE_ON)
            icon.add_style("margin-left: 10px")
            div.add(icon)
            div.add("%s" %title)

            span = SpanWdg()
            span.add_style("font-size: 9px")
            span.add_style("opacity: 0.2")
            span.add(" <i>(%s)</i>" % language)
            div.add(span)

            div.add_event("onmouseover", "this.style.background='%s'" % hover_color)
            div.add_event("onmouseout", "this.style.background='%s'" % bg_color)


            behavior = {
                'type': 'click_up',
                'editor_id': self.editor_id, 
                'cbjs_action': 'spt.script_editor.display_script_cbk(evt, bvr)',
                'code': script.get_code()
            }
            div.add_behavior(behavior)
        """


        widget.add(script_div)

        return widget


    def get_onload_js(self):
        
        return r'''

if (spt.script_editor) {
    return;
}

spt.Environment.get().add_library("spt_script_editor");

spt.script_editor = {}

spt.script_editor.display_script_cbk = function(evt, bvr)
{
    var code = bvr.code;
    var editor_id = bvr.editor_id;
    var script_path = bvr.script_path;
    var script = bvr.script;


    var server = TacticServerStub.get();

    var search_type = "config/custom_script";
    var filters;

    if (script_path) {
        var parts = script_path.split("/");
        var title = parts.pop();
        var folder = parts.join("/");
        filters = [ ['folder', folder], ['title', title] ]
    }
    else {
        filters = [ ['code', code] ];
    }

    if (!script) {
        script = server.query(search_type, {filters:filters, single:true} );
    }
  

    var script_text = script['script'];
    var script_folder = script['folder'];
    var script_title = script['title'];
    var script_code = script['code'];
    var script_language = script['language'];
    if (!script_language) {
        script_langauge = 'javascript';
    }

    var top = bvr.top;
    if (!top) {
        if (bvr.src_el.hasClass('spt_script_editor_top'))
            top = bvr.src_el;
        else    
            top = bvr.src_el.getParent(".spt_script_editor_top");
    }
    top.getElement(".spt_code").value = script_code;
    top.getElement(".spt_folder").value = script_folder;
    top.getElement(".spt_title").value = script_title;
    top.getElement(".spt_language").value = script_language;

    if (editor_id)
    {
        spt.ace_editor.set_editor(editor_id);
    }

    if (script_text) {
        spt.ace_editor.set_value(script_text);
    }
 
    if (script_language) {
        spt.ace_editor.set_language(script_language);
    }

    //editAreaLoader.setValue("shelf_script", script_text);
    //editAreaLoader.setSelectionRange("shelf_script", 0, 0);
    //document.id("shelf_script").value = script_text;
}



spt.script_editor.save_script_cbk = function(evt, bvr)
{
    var server = TacticServerStub.get();
    var search_type = "config/custom_script";

    var top = bvr.src_el.getParent(".spt_script_editor_top");
    var code = top.getElement(".spt_code").value;
    var folder = top.getElement(".spt_folder").value;
    var title = top.getElement(".spt_title").value;
    var language = top.getElement(".spt_language").value;

    if (!language) language = 'javascript';
    if (!folder) folder = 'default';
    if (!title) {
        spt.alert("Please provide a path for this script");
        return;
    }
    // replace leading /
    title = title.replace(/^\/+/,"");
    top.getElement(".spt_title").value = title;

    spt.ace_editor.set_editor(bvr.editor_id);
    var editor = spt.ace_editor.editor;
    var document = editor.getSession().getDocument()
    var value = document.getValue();
    //var value = editAreaLoader.getValue("shelf_script");

    var data = {
        'title': title,
        'folder': folder,
        'script': value,
        'language': language
    }

    server.start({'title': 'Script Editor', 'description': 'Saved Script ['+title+']'});

    var script_sobj;
    if (code == "") {
        script_sobj = server.insert(search_type, data);
    }
    else {
        var search_key = server.build_search_key(search_type, code);
        script_sobj = server.update(search_key, data);
    }
    server.finish();

    // remember the script value
    //var script_text = document.id("shelf_script").value;

    // destroy before reloading
    spt.ace_editor.editor.destroy();
    
    // refresh
    var panel = bvr.src_el.getParent(".spt_panel");
    spt.panel.refresh(panel, null, { callback: function() {
        bvr.script = script_sobj;
        var bvr2 = {script: script_sobj};
        bvr2.top = top;
        spt.script_editor.display_script_cbk({}, bvr2);
    } } );
}



        '''




class ScriptDirListWdg(DirListWdg):

    def init(self):
        self.kwargs['background'] = "background3"
        super(ScriptDirListWdg, self).init()



    def get_file_icon(self, dir, item):
        return ""

    def get_dir_icon(self, dir, item):
        return "FAS_FOLDER"




    def add_top_behaviors(self, top):

        top.add_relay_behavior( {
            'type': 'mouseup',
            'editor_id': self.kwargs.get("editor_id"),
            'bvr_match_class': "spt_script_item",
            'cbjs_action': '''
            bvr.code = bvr.src_el.getAttribute("spt_script_code");
            path = bvr.src_el.getAttribute("spt_path")
            spt.script_editor.display_script_cbk(evt, bvr)
            ''',
        } )

    def add_file_behaviors(self, item_div, dirname, basename):
        item_div.add_class("spt_script_item")
        if not dirname:
            path = "///%s" % (basename)
        else:
            path = "%s/%s" % (dirname, basename)
        
        scripts = self.kwargs.get("scripts")
        script = scripts.get(path)
        if not script:
            item_div.add_style("background-color", "red")
            item_div.add_behavior({"type": "click_up",
                                 "cbjs_action" : '''spt.alert("Please remove leading / in this script path's Title attribute by using the Manage button.")'''})
            item_div.add_attr("title", "Please remove special characters like / in this script path")
            return
           
        script_code = script.get("code")
        language = script.get("language")
        item_div.add_attr("spt_script_code", script_code)
        item_div.add_style("background", "transparent")

        if language:
            span = SpanWdg()
            span.add_style("font-size: 9px")
            span.add_style("opacity: 0.2")
            bgcolor = "black"
            font_color = 'white'
            if language == 'python':
                icon = 'Py'
                bgcolor = "blue"
            elif language == 'javascript':
                icon = "JS"
                bgcolor = "darkorange"
                font_color = 'black'
            elif language == 'server_js':
                icon = 'Se'
            elif language == 'expression':
                icon = 'Ex'
            elif language == 'XML':
                icon = 'Xm'
            else:
                icon = 'NA'
            span.add("<i>%s</i>" % icon)
            span.add_class("spt_script_item_icon")
            span.add_style("background", bgcolor)
            span.add_style("color", font_color)
            style = HtmlElement.style()
            style.add('''
            .spt_script_item_icon{
                border-radius: 10px;
                border: 1px solid black;
                padding: 2px;
                color: #fff;
                background: black;
            }
            ''') 
            span.add(style)
            
            item_div.add(span)


 

class ShelfEditWdg(ScriptEditorWdg):
    pass




__all__.append("AceEditorWdg")
class AceEditorWdg(BaseRefreshWdg):

    def init(self):
        from pyasm.web import HtmlElement
        self.text_area = HtmlElement.div()
        self.text_area.add_class("spt_ace_editor")

        self.editor_id = self.kwargs.get("editor_id")
        if self.editor_id:
            self.unique_id = self.text_area.set_id(self.editor_id)
        else:
            self.unique_id = self.text_area.set_unique_id()
            self.editor_id = self.unique_id


    def get_editor_id(self):
        return self.editor_id

    def get_display(self):
        web = WebContainer.get_web()

        top = self.top
        top.add_class("spt_ace_editor_top")
        
        form_element_name = self.kwargs.get("form_element_name")
        if form_element_name:
            top.add_attr("spt_ace_element_name", form_element_name)

        script = self.kwargs.get("custom_script")
        if script:
            language = script.get_value("language")
        else:
            language = self.kwargs.get("language")
            if not language:
                language = 'javascript'

        code = self.kwargs.get("code")
        if not code:
            code = ""

        dynamic_height = self.kwargs.get("dynamic_height") or False


        show_options = self.kwargs.get("show_options")
        if show_options in ['false', False]:
            show_options = False
        else:
            show_options = True

        options_div = DivWdg()
        top.add(options_div)
        if not show_options:
            options_div.add_style("display: none")
        options_div.add_color("background", "background3")
        options_div.add_border()
        options_div.add_style("text-align: center")
        options_div.add_style("padding: 2px")



        select = SelectWdg("language")
        select.add_style("width: 100px")
        select.add_style("display: inline")
        options_div.add(select)
        select.add_class("spt_language")
        select.set_option("values", "javascript|server_js|python|expression|xml")
        select.add_behavior( {
            'type': 'change',
            'editor_id': self.get_editor_id(),
            'cbjs_action': '''
            spt.ace_editor.set_editor(bvr.editor_id);
            var value = bvr.src_el.value;
            spt.ace_editor.set_language(value);

            //register_change(bvr);

            '''
        } )

        # check if a font size is set in project settings
        font_size = ProjectSetting.get_value_by_key("editor_font_size") or "9pt"

        select = SelectWdg("font_size")
        select.add_style("width: 100px")
        select.add_style("display: inline")
        options_div.add(select)
        select.set_option("labels", "8 pt|9 pt|10 pt|11 pt|12 pt|14 pt|16 pt")
        select.set_option("values", "8pt|9pt|10pt|11pt|12pt|14pt|16pt")
        select.set_value(font_size)
        select.add_behavior( {
            'type': 'change',
            'editor_id': self.get_editor_id(),
            'cbjs_action': '''
            spt.ace_editor.set_editor(bvr.editor_id);
            var editor = spt.ace_editor.editor;
            var editor_id = spt.ace_editor.editor_id;
            var value = bvr.src_el.value;
            
            editor.setFontSize(value);
            //editor.resize();
            '''
        } )



        select = SelectWdg("keybinding")
        select.add_style("width: 100px")
        select.add_style("display: inline")
        options_div.add(select)
        select.set_option("labels", "Ace|Vim|Emacs|Sublime")
        select.set_option("values", "ace|vim|emacs|sublime")
        select.set_value("ace")
        select.add_behavior( {
            'type': 'change',
            'editor_id': self.get_editor_id(),
            'cbjs_action': '''
            spt.ace_editor.set_editor(bvr.editor_id);
            var editor = spt.ace_editor.editor;
            var editor_id = spt.ace_editor.editor_id;
            var value = bvr.src_el.value;
            var keyboard_handler = "";
            
            if(value == "ace")
                keyboard_handler = null;
            else
                keyboard_handler = "ace/keyboard/" + bvr.src_el.value;
            
            editor.setKeyboardHandler(keyboard_handler)
            '''
        } )


        editor_div = DivWdg()
        top.add(editor_div)


        if code:
            load_div = DivWdg()
            top.add(load_div)
            readonly = self.kwargs.get("readonly")
            if readonly in ['true', True]:
                readonly = True
            else:
                readonly = False

            load_div.add_behavior( {
                'type': 'load',
                'code': code,
                'dynamic_height': dynamic_height,
                'language': language,
                'editor_id': self.get_editor_id(),
                'readonly': readonly,
                'cbjs_action': '''
                spt.ace_editor.set_editor(bvr.editor_id);
                
                var set_max_lines = function (editor) {
                    spt.ace_editor.set_editor_top(editor.container.getParent(".spt_ace_editor_top"));
                    doc = spt.ace_editor.get_document();
                    length = doc.getLength()
                    maxLines = length + 10;
                    editor.setOptions({
                        maxLines: maxLines
                    });
                }

                var func = function() {
                    spt.ace_editor.set_editor(bvr.editor_id);
                    var editor = spt.ace_editor.editor;
                    var document = editor.getSession().getDocument();
                    if (bvr.code) {
                        spt.ace_editor.set_value(bvr.code);
                    }
                    spt.ace_editor.set_language(bvr.language);
                    editor.setReadOnly(bvr.readonly);
                    
                    if (bvr.dynamic_height) {
                        editor.on("change", function(event, obj) {
                            set_max_lines(obj); 
                        });
                        set_max_lines(editor);
                    }
                };

                var editor = spt.ace_editor.editor;
                if (!editor) {
                    setTimeout( func, 2000);
                }
                else {
                    func();
                }


                '''
            } )




        # theme
        select = SelectWdg("theme")
        select.add_style("width: 100px")
        select.add_style("display: inline")
        options_div.add(select)
        select.set_option("labels", "Eclipse|Twilight|TextMate|Vibrant Ink|Merbivore|Clouds")
        select.set_option("values", "eclipse|twilight|textmate|vibrant_ink|merbivore|clouds")
        select.set_value("twilight")
        select.add_behavior( {
            'type': 'change',
            'editor_id': self.get_editor_id(),
            'cbjs_action': '''
            spt.ace_editor.set_editor(bvr.editor_id);
            var editor = spt.ace_editor.editor;
            var editor_id = spt.ace_editor.editor_id;
            value = bvr.src_el.value;

            editor.setTheme("ace/theme/" + value);
            '''
        } )


        editor_div = DivWdg()
        top.add(editor_div)

        top.add("<style>.spt_ace_editor_top div { font-family: courier new; }</style>")




        # self.text_area.add_border()
        editor_div.add(self.text_area)


        size = web.get_form_value("size")
        if size:
            width, height = size.split(",")
        else:
            width = self.kwargs.get("width")
            if not width:
                width = "650px"
            height = self.kwargs.get("height")
            if not height:
                height = "500px"
        self.text_area.add_style("width: %s" % width)
        self.text_area.add_style("height: %s" % height)


        show_bottom = self.kwargs.get("show_bottom")
        if show_bottom == None:
            show_bottom = True
        if show_bottom in [True, "true"]:
            bottom_div = DivWdg()
            top.add(bottom_div)
            bottom_div.add_color("background", "background3")
            bottom_div.add_style("position", "relative")
            # bottom_div.add_border()
            bottom_div.add_style("text-align: center")
            bottom_div.add_style("padding: 2px")
            # bottom_div.add_style("height: 20px")

            bottom_title = "Script Editor "
            bottom_div.add(bottom_title)

            hidden = TextWdg("size")
            bottom_div.add(hidden)
            hidden.add_style("width: 85px")
            hidden.add_style("text-align: center")
            hidden.add_class("spt_size")
            hidden.set_value("%s,%s" % (width, height))

            icon = IconWdg("Resize Editor", IconWdg.RESIZE_CORNER)
            icon.add_style("position", "absolute")
            icon.add_style("right", "3px")
            icon.add_style("bottom", "3px")
            bottom_div.add(icon)
            icon.add_style("cursor: se-resize")
            icon.add_behavior( {
                'type': 'drag',
                "cb_set_prefix": 'spt.ace_editor.drag_resize',
            } )

        theme = top.get_theme()
        if theme == 'dark':
            theme = 'twilight'
        else:
            theme = 'eclipse'

        top.add_behavior( {
            'type': 'load',
            'unique_id': self.get_editor_id(),
            'theme': theme,
            'font_size': font_size,
            'cbjs_action': '''

if (typeof(ace) == 'undefined') {

// fist time loading
spt.ace_editor = {}
spt.ace_editor.editor = null;
spt.ace_editor.editor_id = bvr.unique_id;
spt.ace_editor.theme = bvr.theme;


spt.ace_editor.set_editor = function(editor_id) {
    spt.ace_editor.editor_id = editor_id;
    spt.ace_editor.editor = document.id(editor_id).editor;
}

spt.ace_editor.set_editor_top = function(top_el) {
    if (!top_el.hasClass("spt_ace_editor")) {
        top_el = top_el.getElement(".spt_ace_editor");
    }

    var editor_id = top_el.getAttribute("id");
    spt.ace_editor.set_editor(editor_id);
}




spt.ace_editor.get_editor = function() {
    return spt.ace_editor.editor;

}



spt.ace_editor.clear_selection = function() {
    var editor = spt.ace_editor.editor;
    editor.clearSelection();

}



spt.ace_editor.get_selection = function() {
    var editor = spt.ace_editor.editor;
    //return editor.getSelection();
    return editor.getCopyText();
}





spt.ace_editor.get_value = function() {
    var editor = spt.ace_editor.editor;
    var document = editor.getSession().getDocument()
    var value = document.getValue();
    return value;
}



spt.ace_editor.set_value = function(value) {
    var editor = spt.ace_editor.editor;
    var document = editor.getSession().getDocument()
    document.setValue(value);
    editor.gotoLine(2);
    editor.resize();
    editor.focus();
}

spt.ace_editor.goto_line = function(number) {
    var editor = spt.ace_editor.editor;
    var document = editor.getSession().getDocument()
    editor.gotoLine(2);
    editor.resize();
    editor.focus();
 

}


spt.ace_editor.insert = function(value) {
    var editor = spt.ace_editor.editor;
    var position = editor.getCursorPosition();
    var doc = editor.getSession().getDocument()
    doc.insertInLine(position, value);
}

 
spt.ace_editor.insert_lines = function(values) {
    var editor = spt.ace_editor.editor;
    var position = editor.getCursorPosition();
    var doc = editor.getSession().getDocument()
    doc.insertLines(position.row, values);
}



spt.ace_editor.get_document = function() {
    var document = spt.ace_editor.editor.getSession().getDocument()
    return document;

}




spt.ace_editor.set_language = function(value) {
    if (!value) {
        value = 'javascript';
    }

    var editor = spt.ace_editor.editor;
    var top = document.id(spt.ace_editor.editor_id).getParent(".spt_ace_editor_top");
    var lang_el = top.getElement(".spt_language");

    for ( var i = 0; i < lang_el.options.length; i++ ) {
        if ( lang_el.options[i].value == value ) {
            lang_el.options[i].selected = true;
            break;
        }
    }



    var session = editor.getSession();
    var mode;
    if (value == 'python') {
        mode = require("ace/mode/python").Mode;
    }
    else if (value == 'xml') {
        mode = require("ace/mode/xml").Mode;
    }
    else if (value == 'expression') {
        mode = require("ace/mode/xml").Mode;
    } else if (value == 'html') {
        mode = require("ace/mode/html").Mode;
    } else if (value == 'css') {
        mode = require("ace/mode/css").Mode;
    } else {
        mode = require("ace/mode/javascript").Mode;
    }
    session.setMode( new mode() );

    // Extra features
    if (value == "python") {
        session.setUseWrapMode(true);
        session.setWrapLimitRange(80, 80);
    } else {
        session.setUseWrapMode(false);
    }
    editor.setShowPrintMargin(false);

}

spt.ace_editor.drag_start_x;
spt.ace_editor.drag_start_y;
spt.ace_editor.drag_size;
spt.ace_editor.drag_editor_el;
spt.ace_editor.drag_size_el;
spt.ace_editor.drag_resize_setup = function(evt, bvr, mouse_411)
{
    var editor = spt.ace_editor.editor;
    var editor_id = spt.ace_editor.editor_id;

    spt.ace_editor.drag_start_x = mouse_411.curr_x;
    spt.ace_editor.drag_start_y = mouse_411.curr_y;

    var editor_el = document.id(editor_id);
    spt.ace_editor.drag_editor_el = editor_el;
    spt.ace_editor.drag_size = editor_el.getSize();

    var top = bvr.src_el.getParent(".spt_ace_editor_top");
    spt.ace_editor.drag_size_el = top.getElement(".spt_size");
}


spt.ace_editor.drag_resize_motion = function(evt, bvr, mouse_411)
{
    var diff_x = parseFloat(mouse_411.curr_x - spt.ace_editor.drag_start_x);
    var diff_y = parseFloat(mouse_411.curr_y - spt.ace_editor.drag_start_y);

    var size = spt.ace_editor.drag_size;


    var editor_el = spt.ace_editor.drag_editor_el;

    var width = size.x + diff_x
    if (width < 300) {
        width = 300;
    }
    var height = size.y + diff_y
    if (height < 200) {
        height = 200;
    }

    editor_el.setStyle("width", width);
    editor_el.setStyle("height", height);

    spt.ace_editor.drag_size_el.value = width + "," + height;

    var editor = spt.ace_editor.editor;
    editor.resize();

}

   

    var ace_setup =  function() {
        var editor = ace.edit(bvr.unique_id, {'minLines': 10});
        spt.ace_editor.editor = editor;

        // put the editor into the dom
        spt.ace_editor.editor_id = bvr.unique_id;
        document.id(bvr.unique_id).editor = editor;

        editor.setTheme("ace/theme/" + spt.ace_editor.theme);
        
        try {
            var JavaScriptMode = require("ace/mode/javascript").Mode;
            editor.getSession().setMode(new JavaScriptMode())
        } catch(err) {
            log.critical("Mode files not loaded");
        }
    }

 


     var js_files = [
        "/context/spt_js/ace/ace-1.4.7/src/ace.js",
        //"ace/ace-1.4.7/src/ace-uncompressed.js",
    ];

   


    spt.dom.load_js(js_files, function() { 
    
        ace; require; define; 

        var core_js_files = [
            "/context/spt_js/ace/ace-1.4.7/src/mode-javascript.js",
            "/context/spt_js/ace/ace-1.4.7/src/mode-xml.js",
            "/context/spt_js/ace/ace-1.4.7/src/mode-python.js",
            "/context/spt_js/ace/ace-1.4.7/src/mode-html.js",
            "/context/spt_js/ace/ace-1.4.7/src/mode-css.js",
            "/context/spt_js/ace/ace-1.4.7/src/theme-twilight.js",
            "/context/spt_js/ace/ace-1.4.7/src/theme-textmate.js",
            "/context/spt_js/ace/ace-1.4.7/src/theme-vibrant_ink.js",
            "/context/spt_js/ace/ace-1.4.7/src/theme-merbivore.js",
            "/context/spt_js/ace/ace-1.4.7/src/theme-clouds.js",
            "/context/spt_js/ace/ace-1.4.7/src/theme-eclipse.js"
        ];
        
        //require(core_js_files, ace_setup);
        spt.dom.load_js(core_js_files, ace_setup);
        
        //spt.dom.load_js(supp_js_files);      
    });
   

    





}
else {
    var editor = ace.edit(bvr.unique_id, {'minLines': 10});
    editor.setTheme("ace/theme/" +  bvr.theme);
    var JavaScriptMode = require("ace/mode/javascript").Mode;
   
    editor.getSession().setMode(new JavaScriptMode())

    spt.ace_editor.editor_id = bvr.unique_id;
    spt.ace_editor.editor = editor;
    document.id(bvr.unique_id).editor = editor;
    spt.ace_editor.editor.setFontSize(bvr.font_size);


}
            '''
        } )


        return top


    def get_buttons_wdg(self):

        button_div = DivWdg()

        button = ActionButtonWdg(title='Run')
        button_div.add(button)
        button.add_style("float: left")
        button.add_behavior( {
            'type': 'click_up',
            'cbjs_action': '''

            var top = bvr.src_el.getParent(".spt_script_editor_top");
            var code = top.getElement(".spt_code").value;
            var folder = top.getElement(".spt_folder").value;
            var title = top.getElement(".spt_title").value;
            var language = top.getElement(".spt_language").value;

            spt.ace_editor.set_editor_top(top);
            var editor = spt.ace_editor.editor;
            var value = editor.getSession().toString();

            try {
                if (language == 'javascript') {
                    eval(value);
                } 
                else if (language == 'expression') {
                    var server = TacticServerStub.get();
                    var ret_val;
                   
                        ret_val = server.eval(value);

                    if (ret_val && ret_val.length) {
                        for (var i = 0; i < ret_val.length; i++) {
                            log.critical(ret_val[i]);
                        }
                    }
                    else {
                        log.critical(ret_val);
                    }
                } 
                else if (language == 'python') {
                    var path = folder + "/" + title;
                    var server = TacticServerStub.get();
                    var info = server.execute_python_script(path);
                    log.critical(info);
                }
                else if (language == 'server_js') {
                    var path = folder + "/" + title;
                    var server = TacticServerStub.get();
                    var info = server.execute_js_script(path);
                    log.critical(info);
                }
                else {
                    var ok = function() { eval(value);}
                    spt.confirm("Please set the language of this script. It's assumed to be javascript if left blank. Continue to run?", ok, null);
                   
                } 
            } catch(e) {
                spt.error(spt.exception.handler(e));
            }

            '''
        } )

        button = ActionButtonWdg(title='Save')
        button_div.add(button)
        button.add_style("float: left")
        button.add_behavior( {
            'type': 'click_up',
            'editor_id': self.unique_id,
            'cbjs_action': '''
            /*
            if (!has_changes(bvr)) {
                spt.alert("No changes have been made");
                return;
            }
            */

            var top = bvr.src_el.getParent(".spt_script_editor_top");

            spt.app_busy.show("Saving Script ...");
            setTimeout(function() {
                spt.ace_editor.set_editor_top(top);
                spt.script_editor.save_script_cbk(evt, bvr);
                spt.app_busy.hide();
            }, 10);

            '''
        } )
       
 
        button = ActionButtonWdg(title='Clear')
        button_div.add(button)
        button.add_style("float: left")
        button.add_behavior( {
            'type': 'click_up',
            'cbjs_action': '''
            var top = bvr.src_el.getParent(".spt_script_editor_top");
           
            // Clear script path
            var path_inputs = top.getElement(".spt_script_path");
            spt.api.Utility.clear_inputs(path_inputs);

            // Clear ace editor
            spt.ace_editor.set_editor_top(top);
            var editor = spt.ace_editor.editor;
            var document = editor.getSession().getDocument()
            document.setValue("");
            '''
        } )
       

        button = ActionButtonWdg(title='Resize')
        #button_div.add(button)
        button.add_behavior( {
            'type': 'click_up',
            'cbjs_action': '''
            var editor = spt.ace_editor.editor;
            var editor_id = spt.ace_editor.editor_id;
            document.id(editor_id).setStyle("width", "1000px");
            document.id(editor_id).setStyle("height", "800px");
            editor.resize();

            '''
        } )
       
        return button_div
