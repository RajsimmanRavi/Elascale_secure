import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import uuid
from util import *


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
            write_file(message)
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
    Basically calls the get_micro and get_macro to fetch the current running services and VMs.
    Then, it reads the ini files to get their current config parameter values.
    It sends them both to index.html to render that content.
"""

class MainHandler(BaseHandler):
    def get(self):

        if not self.current_user:
            self.redirect("/login")
            return

        client = docker.from_env()

        micro = get_micro(client)
        macro = get_macro(client)

        # Read ini files
        micro_config = read_file(os.environ['MICRO'])
        macro_config = read_file(os.environ['MACRO'])

        # add any newly running services to the INI files
        micro = get_final_list(micro,micro_config, "micro")
        macro = get_final_list(macro, macro_config, "macro")

        # Read ini files again to load newly added services
        micro_config = read_file(os.environ['MICRO'])
        macro_config = read_file(os.environ['MACRO'])

        #Get the IP address of the server from the Environment variables
        ip_addr = os.environ['HOST_IP']
        elastic_ip = os.environ['ELASTIC_IP']

        #Get the Kibana links from elastic search. This will be a dictionary
        #Eg. kibana_links["title_of_dashboard"] = "http://..."
        kibana_links = get_kibana_links(elastic_ip)


        self.render("index.html", micro_services=micro, macro_services=macro, micro_config=micro_config, macro_config=macro_config, ip_addr=ip_addr, kibana_links=kibana_links)
        sys.stdout.flush()

class LoginHandler(BaseHandler):
    def get(self):

        self.render("login.html")
        sys.stdout.flush()
    def post(self):

        if check_password(self.get_argument("name"),self.get_argument("password")):
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

    """
    os.environ['HOST_IP']       = "10.11.1.24"
    os.environ['HOST_PORT']     = "8888"
    os.environ['ELASTIC_IP']    = "10.11.1.24"
    os.environ['MICRO']         = "/home/ubuntu/Elascale/config/microservices.ini"
    os.environ['MACRO']         = "/home/ubuntu/Elascale/config/macroservices.ini"
    os.environ['SELF_CERT']     = "/home/ubuntu/Elascale_UI/certs/elascaleUI_certificate.pem"
    os.environ['SELF_KEY']      = "/home/ubuntu/Elascale_UI/certs/elascale_ui_private_key.pem"
    os.environ['NGINX_CERT']    = "/etc/nginx/ssl/elasticsearch_certificate.pem"
    os.environ['USERNAME']      = "xxx"
    os.environ['PASSWORD']      = "xxx"
    """
    http_server = tornado.httpserver.HTTPServer(Application(), ssl_options={
        "certfile": os.environ['SELF_CERT'],
        "keyfile": os.environ['SELF_KEY'],
    })
    http_server.listen(os.environ['HOST_PORT']) # This is for the final version
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
