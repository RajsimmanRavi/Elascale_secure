import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import sys
import uuid
import autoscaler.conf.engine_config as eng
from autoscaler.ui import util

"""
    Class to fetch cookie of current user
"""
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

"""
   Class to handle the /config.
   Basically writes the new values to the appropriate ini file.
   Returns the success/error msg.
"""
class ConfigHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("Websocket opened")
        sys.stdout.flush()

    def on_message(self, message):

        try:
            util.write_file(message)
        except Exception as e:
            self.write_message(str(e))
        else:
            message = "Values have been modified successfully! "
            message += "Press OK to view the changes!"
            self.write_message(message)

    def on_close(self):
        print("Websocket closed")
        sys.stdout.flush()

"""
    Class to handle / .
    It sends currently running micro/macroservices to index.html to render that content.
"""
class MainHandler(BaseHandler):
    def get(self):

        if not self.current_user:
            req = self.request
            if req.headers.get('X-Forwarded-Proto') != 'https':
                self.handler_class = tornado.web.RedirectHandler
                self.handler_kwargs = {'url': 'https://%s%s' % (req.headers['Host'], req.uri)}

            self.redirect("/login")
            return

        # Read ini files
        micro_config = util.read_file(eng.MICRO_CONFIG)
        macro_config = util.read_file(eng.MACRO_CONFIG)

        # Get current micro/macroservices
        micro = micro_config.sections()
        macro = macro_config.sections()

        ip_addr = eng.UI_IP
        elastic_ip = eng.ELASTIC_IP

        #Get the Kibana links from elastic search. This will be a dictionary
        #Eg. kibana_links["title_of_dashboard"] = "http://..."
        kibana_links = util.get_kibana_links(elastic_ip, eng.NGINX_CERT)

        self.render("index.html", micro_services=micro, macro_services=macro, micro_config=micro_config, macro_config=macro_config, ip_addr=ip_addr, kibana_links=kibana_links, elastic_ip=elastic_ip)
        sys.stdout.flush()

class LoginHandler(BaseHandler):
    def get(self):

        self.render("login.html")
        sys.stdout.flush()

    def check_password(self, username, password):
        if username == eng.UI_USERNAME and password == eng.UI_PASSWORD :
            return True
        else:
            return False

    def post(self):

        if self.check_password(self.get_argument("name"),self.get_argument("password")):
            self.set_secure_cookie("user", self.get_argument("name"))
            self.redirect("/")
        else:
            self.redirect("/login")

class Application(tornado.web.Application):
    def __init__(self):
        """
        initializer for application object
        """
        handlers = [
            (r"/", MainHandler),
            (r"/config", ConfigHandler),
            (r"/login", LoginHandler),
	    ]

        settings = {
	        "debug": True,
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "cookie_secret": str(uuid.uuid4()),
            "xsrf_cookies": True,
            "login_url": "/login",
	    }

        tornado.web.Application.__init__(self,handlers,**settings)
        sys.stdout.flush()


def main():

    http_server = tornado.httpserver.HTTPServer(Application(), ssl_options={
        "certfile": eng.UI_SELF_CERT,
        "keyfile": eng.UI_SELF_KEY,
    })
    http_server.listen(port = eng.UI_PORT) # This is for the final version
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
