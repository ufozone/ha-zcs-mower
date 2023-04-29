# The MIT License (MIT)
#
# Copyright 2017 Telit
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from httplib2 import Http
import simplejson as json

class TR50http(object):
    # The API endpoint for POSTing (e.g. https://www.example.com/api)
    endpoint = ""

    # The application identifier you will be using.
    app_id = ""

    # The application token.
    app_token = ""

    # The thing key used to identify the application.
    thing_key = ""

    # The username used to connect to the server.
    username = ""

    # The password used to connect to the server.
    password = ""

    # Last JSON string received from the endpoint. Used when debugging.
    last_received = ""

    # Last JSON string sent to the endpoint. Used when debugging.
    last_sent = ""

    # If the last request succeeded or failed.
    last_status = None

    # Holds the response data from the api call.
    response = []

    # Holds the current session identifier.
    session_id = ""

    # Holds any error returned by the api.
    error = []


    # Initialize the object.
    # @param    dict    options    The initialization options.
    def __init__(self, options = {}):
        """Initialize the object."""
        if "endpoint" in options:
            self.endpoint = options["endpoint"]

        if "app_id" in options:
            self.app_id = options["app_id"]
        if "app_token" in options:
            self.app_token = options["app_token"]
        if "thing_key" in options:
            self.thing_key = options["thing_key"]

        if "username" in options:
            self.username = options["username"]
        if "password" in options:
            self.password = options["password"]

        if "session_id" in options:
            self.session_id = options["session_id"]

        if (len(self.session_id) == 0) or (self.execute("diag.ping") == False):
            self.session_id = ""
            self.auth()


    # This method sends the TR50 request to the server and parses the response.
    # @param    mixed    json_string     The JSON command and arguments. This parameter can also be a dict that will be converted to a JSON string.
    # @return   bool     Success or failure to post.
    def post(self, json_string):
        """This method sends the TR50 request to the server and parses the response."""
        self.error         = ""
        self.last_status   = True
        self.last_received = ""
        self.response      = ""

        json_string = self.set_json_auth(json_string)
        self.last_sent = json_string

        http_obj = Http(disable_ssl_certificate_validation = True)
        result, self.last_received = http_obj.request(self.endpoint, "POST", json_string)
        if not result["status"] == "200":
            raise Exception("Failed to POST to %s" % self.endpoint)

        self.response = json.loads(self.last_received)

        if "errorMessages" in self.response:
            self.error = self.response["errorMessages"]

        if "success" in self.response:
            self.last_status = self.response["success"]

        return self.last_status


    # Return the response data for the last command if the last command was successful.
    # @return    dict    The response data.
    def get_response(self):
        """Return the response data for the last command if the last command was successful."""
        if self.last_status and len(self.response["data"]) > 0:
            return self.response["data"]
        return None


    # This method checks the JSON command for the auth parameter. If it is not set, it adds.
    # @param    mixed    json_string    A JSON string or the dict representation of JSON.
    # @return   string   A JSON string with the auth parameter.
    def set_json_auth(self, json_string):
        """This method checks the JSON command for the auth parameter. If it is not set, it adds."""
        if not type(json_string) is dict:
            json_string = json.loads(json_string)

        if not "auth" in json_string:
            if len(self.session_id) == 0:
                self.auth()
            # if it is still empty, we cannot proceed
            if len(self.session_id) == 0:
                raise Exception("Authorization failed. Please check the application configuration.")
            json_string["auth"] = { "sessionId" : self.session_id }

        json_string = json.dumps(json_string)
        return json_string


    # Package the command and the params into an array and sends the command to the configured endpoint for processing.
    # @param    command    string    The TR50 command to execute.
    # @param    params     dict      The command parameters.
    # @return   bool       Success or failure to post.
    def execute(self, command, params = False):
        """Package the command and the params into an array and sends the command to the configured endpoint for processing."""
        if command == "api.authenticate":
            parameters = { "auth" : { "command" : "api.authenticate", "params" : params } }
        else:
            parameters = { "data" : { "command" : command } }
            if not params == False:
               parameters["data"]["params"] = params
        return self.post(parameters)


    # Depending on the configuration, authenticate the app or the user, prefer the app.
    # @return    bool    Success or failure to authenticate.
    def auth(self):
        """Depending on the configuration, authenticate the app or the user, prefer the app."""
        if len(self.app_id) > 0 and len(self.app_token) > 0 and len(self.thing_key) > 0:
            return self.app_auth(self.app_id, self.app_token, self.thing_key)
        elif len(self.username) > 0 and len(self.password) > 0:
            return self.user_auth(self.username, self.password)
        return False



    # Authenticate the application.
    # @param     string    app_id                The application ID.
    # @param     string    app_token             The application token.
    # @param     string    thing_key             The key of the application's thing.
    # @param     bool      update_session_id     Update the object session ID.
    # @return    bool      Success or failure to authenticate.
    def app_auth(self, app_id, app_token, thing_key, update_session_id = True):
        """Authenticate the application."""
        params = { "appId" : app_id, "appToken" : app_token, "thingKey" : thing_key }
        response = self.execute("api.authenticate", params)
        if response == True:
            if update_session_id:
                self.session_id = self.response["auth"]["params"]["sessionId"]
            return True
        return False


    # Authenticate a user.
    # @param     string    username             The username.
    # @param     string    password             The password.
    # @param     bool      update_session_id    Update the object session ID.
    # @return    bool      Success or failure to authenticate.
    def user_auth(self, username, password, update_session_id = True):
        """Authenticate a user."""
        params = { "username" : username, "password" : password }
        if self.execute("api.authenticate", params):
            if update_session_id:
                self.session_id = self.response["auth"]["params"]["sessionId"]
            return True
        return false


    # Returns an array of the options set in the object. Useful for initializing and existing object of a sub-class.
    # @return    dict    The array of options.
    def get_options(self):
        """Returns an array of the options set in the object. Useful for initializing and existing object of a sub-class."""
        return {
            "endpoint"   : self.endpoint,
            "session_id" : self.session_id,
            "app_id"     : self.app_id,
            "app_token"  : self.app_token,
            "thing_key"  : self.thing_key,
            "username"   : self.username,
            "password"   : self.password
        }


    # After a command is executed, this method returns an array of debugging information about the object and the last command.
    # @return    dict    Debugging data.
    def debug(self):
        """After a command is executed, this method returns an array of debugging information about the object and the last command."""
        return {
            "endpoint"      : self.endpoint,
            "last_sent"     : self.last_sent,
            "last_received" : self.last_received,
            "error"         : self.error
        }
