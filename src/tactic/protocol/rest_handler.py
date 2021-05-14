###########################################################
#
# Copyright (c) 2005-2012, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ['BaseRestHandler', 'TestCustomRestHandler', 'SObjectRestHandler','APIRestHandler']

from pyasm.common import jsonloads, jsondumps, Environment, Container
from tactic.ui.common import BaseRefreshWdg

import re

class BaseRestHandler(BaseRefreshWdg):

    def authenticate(self):
        raise Exception("Must override authenticate")

    def get_display(self):

        method = self.kwargs.get("Method")
        if not method:
            raise Exception("No method specified")

        if method == "GET":
            ret_val = self.GET()
        elif method == "POST":
            ret_val = self.POST()
        elif method == "PUT":
            ret_val = self.PUT()
        elif method == "DELETE":
            ret_val = self.PUT()
        else:
            ret_val = self.GET()

        return ret_val



    def GET(self):
        pass

    def POST(self):
        return self.GET()

    def PUT(self):
        pass

    def DELETE(self):
        pass





class TestCustomRestHandler(BaseRestHandler):

    def GET(self):
        return "Test Custom GET"

    def POST(self):
        return "Test Custom POST"



from tactic_client_lib import TacticServerStub

class SObjectRestHandler(BaseRestHandler):

    def GET(self):
        method = self.kwargs.get("method")
        print(self.kwargs)
        print("method: ", method)
        print("expression: ", self.kwargs.get("expression"))


        # /rest/get_by_code/cars/CAR00009

        # /rest/query?search_type=sthpw/cars
        if method == "query":
            code = self.kwargs.get("data")
            from pyasm.search import Search
            sobject = Search.get_by_code(search_type, code)
            sobject_dict = sobject.get_sobject_dict()
            return sobject_dict

        # /rest/expression/@SOBJECT(sthpw/task)
        elif method == "expression":
            expression = self.kwargs.get("expression")
            server = TacticServerStub.get()
            return server.eval(expression)

        # /rest/simple_checkin?search_key=dfadfdsas&data={}
        elif method == "expression":
            expression = self.kwargs.get("expression")
            server = TacticServerStub.get()
            return server.eval(expression)


        return {}




class APIRestHandler(BaseRestHandler):

    def get_content_type(self):
        return "application/json"


    def get_body(self):
        return self.body


    def get_body(self):

        body = Container.get("REST:body")
        if body == None:
            import cherrypy
            if cherrypy.request.body:
                body = cherrypy.request.body.read()
                if body:
                    body = jsonloads(body.decode())
                    Container.put("REST:body", body)

        return body



    def GET(self):

        return "TACTIC REST Interface"



    def POST(self):

        from pyasm.web import WebContainer
        web = WebContainer.get_web()

        method = web.get_form_value("method")

        # process the data
        data = web.get_form_data()

        body_data = {}

        body = self.get_body()
        if body:
            #print("body: ", body)

            for name, value in body.items():
                if name == "method":
                    method = value
                else:
                    body_data[name] = value



        # make sure there are no special characters in there ie: ()
        p = re.compile('^\w+$')
        if not re.match(p, method):
            raise Exception("Method [%s] does not exist" % method)

        # special handling for get_ticket
        if method == "get_ticket":
            security = Environment.get_security()
            ticket = security.get_ticket_key()
            return ticket
        elif method == "get_ticket_data":
            security = Environment.get_security()
            ticket = security.get_ticket()
            if ticket:
                ticket = ticket.get_value("data")
            return ticket




        from tactic_client_lib import TacticServerStub
        server = TacticServerStub.get()

        if not eval("server.%s" % method):
            raise Exception("Method [%s] does not exist" % method)

        keys = web.get_form_keys()

        args = None
        call = None
        if 'args' in keys:
            args = web.get_form_value('args')
            try:
                args = jsonloads(args)
            except ValueError:
                pass
           
            if isinstance(args, list):
                print("args: %s" % args)
                call = "server.%s(*args)" % method
            

        if not call:
            kwargs = {}

            for key in keys:

                if key in ["method", "login_ticket", "password", "domain"]:
                    continue

                if key == 'kwargs':
                    args = web.get_form_value(key)
                    args = jsonloads(args)
                    for name, value in args.items():
                        kwargs[name] = value
                else:
                    kwargs[key] = web.get_form_value(key)


            for key, value in body_data.items():
                kwargs[key] = value


            print("kwargs: %s" % kwargs)
            call = "server.%s(**kwargs)" % method

        print("call: %s" % call)
        try:
            ret = eval(call)
            return ret
        except Exception as e:
            import cherrypy
            cherrypy.response.status = "405"
            try:
                message = e.message
            except:
                message = e
            return {
                "error": {
                    "args": e.args,
                    "message": message,
                    "type": e.__class__.__name__
                }
            }



