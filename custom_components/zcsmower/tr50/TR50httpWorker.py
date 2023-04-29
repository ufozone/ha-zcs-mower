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

import TR50http
import re

class TR50httpWorker(TR50http.TR50http):

    # Initialize the object.
    # @param    dict    options    The initialization options.
    def __init__(self, options = {}):
        """Initialize the object."""
        TR50http.TR50http.__init__(self, options)


    # Convert a date string to TR50 format.
    # @param     datetime    date_obj   The date string, or the datetime object to be reformatted.
    # @return    string      The date formatted in the style that TR50 requires.
    def tr50_date_format(self, date_obj):
        """Convert a date string to TR50 format."""
        if type(date_obj) is str:
            return date_obj
        else:
            datetime_string = date_obj.strftime("%Y-%m-%dT%H:%M:%S%z")
            tr50_datetime_string = datetime_string[:-2] + ':' + datetime_string[-2:] # 2004-02-12T15:19:21+00:00
            return tr50_datetime_string


    # email.send : Sends an email to one or more email addresses from a registered user's email address in the M2M Service.
    # @param     mixed     email_to         A single email address: 'john.doe@example.com', or an array containing the recipients of the email: [ 'john.doe@example.com', 'jane.doe@example.com' ].
    # @param     mixed     email_from       A single email address: 'jane.doe@example.com', or a dict containing an email address indexed by a name of the user to use as the sender of the email: { 'Jane Doe' : 'jane.doe@example.com' }.
    # @param     string    email_subject    The subject of the email.
    # @param     string    email_body       The body of the email.
    # @return    bool      If the command executes successfully.
    def email_send(self, email_to, email_from, email_subject, email_body):
        """Sends an email to one or more email addresses from a registered user's email address in the M2M Service."""
        params = { "subject" : email_subject, "body" : email_body }

        if type(email_to) is list:
            params["to"] = email_to
        else:
            params["to"] = [ email_to ]

        if isinstance(email_from, dict):
            email_fromKeys = email_from.keys()
            params["fromName"] = email_fromKeys[0]
            params["from"] = email_from[email_fromKeys[0]]
        else:
            params["from"] = email_from

        if re.search("<.+?>", email_body) != None:
            params["html"] = True

        result = self.execute("email.send", params)
        return (result == True and self.response["data"]["success"])


    # locale.get : This command is used to retrieve the current session's locale.
    # @return    mixed    Returns the dict of the session's locale on success, or the failure code.
    def locale_get(self):
        """This command is used to retrieve the current session's locale."""
        result = self.execute("locale.get")
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # locale.list : This command is used to list supported locales.
    # @return    mixed    Returns the dict of the supported locales on success, or the failure code.
    def locale_list(self):
        """This command is used to list supported locales."""
        result = self.execute("locale.list")
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]["result"]
        else:
            return self.response["data"]["success"]


    # locale.set : This command is used to set the current session's locale.
    # @param     string    locale    The locale to set.
    # @return    bool      If the command executes successfully.
    def locale_set(self, locale):
        """This command is used to set the current session's locale."""
        params = { "locale" : locale }
        result = self.execute("locale.set", params)
        return (result == True and self.response["data"]["success"] == True)


    # location.current : This command is used to obtain the last report location for a thing.
    # @param     string    thing_key    Identifies the thing associated with the location entry.
    # @return    mixed     Returns the dict of the thing's current location on success, or the failure code.
    def location_current(self, thing_key):
        """This command is used to obtain the last report location for a thing."""
        params = { "thingKey" : thing_key }
        result = self.execute("location.current", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # location.decode : This command is used to decode a latitude/longitude pair into an address.
    # @param     float    latitude     The latitude of the location.
    # @param     float    longitude    The longitude of the location.
    # @return    mixed    Returns the dict of the address of the latitude/longitude pair on success, or the failure code.
    def location_decode(self, latitude, longitude):
        """This command is used to decode a latitude/longitude pair into an address."""
        params = { "lat" : latitude, "lng" : longitude }
        result = self.execute("location.decode", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # location.encode : This command is used to encode a textual location into a latitude/longitude pair.
    # @param     string    location    The textual location to be encoded.
    # @return    mixed     Returns the dict of the latitude/longitude associated with the provided location on success, or the failure code.
    def location_encode(self, location):
        """This command is used to encode a textual location into a latitude/longitude pair."""
        params = { "location" : location }
        result = self.execute("location.encode", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # location.publish : This command is used to publish the location of a thing.
    # @param     string    thing_key    The unique identifier of the thing to which the location data is to be associated.
    # @param     float     latitude     The latitude for this location publish.
    # @param     float     longitude    The longitude for this location publish.
    # @param     string    date_obj     The timestamp for which the location data is being published.
    # @param     int       heading      The direction for this location publish (in degrees where 0 is North, 90 is East, 180 is South, and 270 is West).
    # @param     int       altitude     The altitude for this location publish.
    # @param     int       speed        The speed for this location publish.
    # @param     int       fix_acc      The accuracy in meters of the coordinates being published.
    # @param     string    fix_type     A string describing the location fixation type. Typically "gps", "gnss", "manual", or "m2m-locate".
    # @param     string    corr_id      A correlation ID that can be used when querying to find related data objects.
    # @return    bool      If the command executes successfully.
    def location_publish(self, thing_key, latitude, longitude, date_obj = False,
                        heading = False, altitude = False, speed = False,
                        fix_acc = False, fix_type = False, corr_id = False):
        """This command is used to publish the location of a thing."""
        params = { "thingKey" : thing_key, "lat" : latitude, "lng" : longitude }
        if (date_obj != False):
            params["ts"] = self.tr50_date_format(date_obj)
        if (heading != False):
            params["heading"] = heading
        if (altitude != False):
            params["altitude"] = altitude
        if (speed != False):
            params["speed"] = speed
        if (fix_acc != False):
            params["fixAcc"] = fix_acc
        if (fix_type != False):
            params["fixType"] = fix_type
        if (corr_id != False):
            params["corrId"] = corr_id
        result = self.execute("location.publish", params)
        return (result == True and self.response["data"]["success"])


    # location.speedlimit : This command is used to find the speed limit at a specified location.
    # @param     float    latitude     The latitude being requested.
    # @param     float    longitude    The longitude being requested.
    # @return    mixed    Returns the dict of the speed limit associated with the provided location on success, or the failure code.
    def location_speedlimit(self, latitude, longitude):
        """This command is used to find the speed limit at a specified location."""
        params = { "lat" : latitude, "lng" : longitude }
        result = self.execute("location.speedlimit", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # location.weather : This command is used to return the weather information at a specified location.
    # @param     float    latitude     The latitude being requested.
    # @param     float    longitude    The longitude being requested.
    # @return    mixed    Returns the dict of the weather information associated with the provided location on success, or the failure code.
    def location_weather(self, latitude, longitude):
        """This command is used to return the weather information at a specified location."""
        params = { "lat" : latitude, "lng" : longitude }
        result = self.execute("location.weather", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # method.exec : This command is used to execute a method of a thing.
    # @param     string    thing_key     Identifies the thing for which the method is executed.
    # @param     string    method        The method to execute.
    # @param     int       ack_timeout   Acknowlege timeout duration in seconds. Default is 30.
    # @param     dict      parameters    Notification variables or method parameters to be passed to the method.
    # @return    bool      If the command executes successfully.
    def method_exec(self, thing_key, method, ack_timeout = False, parameters = False):
        """This command is used to execute a method of a thing."""
        params = { "thingKey" : thing_key , "method" : method }
        if ack_timeout != False:
            params["ackTimeout"] = ack_timeout
        if parameters != False:
            params["parameters"] = parameters
        result = self.execute("method.exec", params)
        return (result == True and self.response["data"]["success"])


    # org.find : This command is used to find and return an organization.
    # @param     string    org_key    The key identifying the organization.
    # @return    mixed     Returns the dict of the organization information on success, or the failure code.
    def org_find(self, org_key):
        """This command is used to find and return an organization."""
        params = { "key" : org_key }
        result = self.execute("org.find", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # org.list : This command is used to return a list of organizations.
    # @param     int      offset                The starting list offset, used for pagination, defaults to 0 if not specified.
    # @param     int      limit                 Limits the number of results returned. Defaults to the maximum configured size.
    # @param     bool     can_have_sub_orgs     Whether to only list organizations that are capable of having child organizations.
    # @return    mixed    Returns an dict of organizations on success, or the failure code.
    def org_list(self, offset = False, limit = False, can_have_sub_orgs = False):
        """This command is used to return a list of organizations."""
        params = {}
        if offset != False:
            params["offset"] = offset
        if limit != False:
            params["limit"] = limit
        if can_have_sub_orgs != False:
             params["canHaveSubOrgs"] = can_have_sub_orgs
        result = self.execute("org.list", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]["result"]
        else:
            return self.response["data"]["success"]


    # property.aggregate : This command is used to obtain historical property data aggregated over a specified time period for a thing.
    # @param     string    thing_key      Identifies the thing to which the property data is to be associated.
    # @param     string    property_key   The key for the property that you wish to aggregate.
    # @param     string    calc           The calculation to use for the aggregation: avg, sum, max, min, count, etc.
    # @param     string    series         The series to be used when grouping property values to aggregate: 'hour' or 'day'.
    # @param     string    start          Timestamp for the start of the specified time window.
    # @param     string    end            Timestamp for the end of the specified time window.
    # @param     bool      split          Set to true if you want the timestamp and value fields to be split into two elements within the dict.
    # @return    mixed     Returns the dict of property aggregation on success, or the failure code.
    def property_aggregate(self, thing_key, property_key, calc, series,
                          start, end, split = False):
        """This command is used to obtain historical property data aggregated over a specified time period for a thing."""
        params = {
            "thingKey" : thing_key,
            "key"      : property_key,
            "calc"     : calc,
            "series"   : series,
            "start"    : self.tr50_date_format(start),
            "end"      : self.tr50_date_format(end),
            "split"    : split
        }
        result = self.execute("property.aggregate", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # property.current : This command is used to retrieve the current value of a property.
    # @param     string    thing_key      Identifies the thing to which the property data is associated.
    # @param     string    property_key   The key for the property that you wish to retrieve.
    # @return    mixed     Returns the dict of current property on success, or the failure code.
    def property_current(self, thing_key, property_key):
        """This command is used to retrieve the current value of a property."""
        params = { "thingKey" : thing_key, "key" : property_key }
        result = self.execute("property.current", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # property.publish : The property.publish command is used to publish property data (typically sensor data) for a thing.
    # @param     string    thing_key      Identifies the thing to which the property data is to be associated.
    # @param     string    property_key   The key for the property that you wish to publish.
    # @param     float     value          The value to publish.
    # @param     string    ts             The timestamp in which the value was recorded.
    # @param     string    corrId         A correlation ID that can be used when querying to find related data objects.
    # @return    bool      If the command executes successfully.
    def property_publish(self, thing_key, property_key, value,
                        date_obj = False, corrId = False):
        """The property.publish command is used to publish property data (typically sensor data) for a thing."""
        params = { "thingKey" : thing_key, "key" : property_key, "value" : value }
        if date_obj != False:
            params["ts"] = self.tr50_date_format(date_obj)
        if corrId != False:
            params["corrId"] = corrId
        result = self.execute("property.publish", params)
        return (result == True and self.response["data"]["success"])


    # session.info : This command is used to obtain information about the current session.
    # @return    mixed    Returns the dict of current session on success, or the failure code.
    def session_info(self):
        """This command is used to obtain information about the current session."""
        result = self.execute("session.info")
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # session.org.list : This command is used to obtain a list of organizations available to the current session.
    # @param     bool     include_roles     Indicate that the available roles are to be returned with the response.
    # @return    mixed    Returns the dict of organizations (and roles) on success, or the failure code.
    def session_org_list(self, include_roles = False):
        """This command is used to obtain a list of organizations available to the current session."""
        params = {}
        if include_roles != False:
            params["includeRoles"] = include_roles
        result = self.execute("session.org.list", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]["result"]
        else:
            return self.response["data"]["success"]


    # session.org.switch : This command is used to switch a session between organizations.
    # @param     string    org_key      The organization key.
    # @return    bool      If the command executes successfully.
    def session_org_switch(self, org_key):
        """This command is used to switch a session between organizations."""
        params = { "key" : org_key }
        result = self.execute("session.org.switch", params)
        return (result == True and self.response["data"]["success"])


    # thing_def.find : This command is used to find an existing thing definition.
    # @param     string    thing_def_key    The key of the thing definition to find.
    # @return    mixed     Returns the dict of the selected thing definition on success, or the failure code.
    def thing_def_find(self, thing_def_key):
        """This command is used to find an existing thing definition."""
        params = { "key" : thing_def_key }
        result = self.execute("thing_def.find", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # thing_def.list : Acquire the list of Thing Definitions.
    # @param     int      offset    The starting list offset, used for pagination, defaults to 0 if not specified.
    # @param     int      limit     Limits the number of results returned. Defaults to the maximum configured size.
    # @return    mixed    Returns the dict of thing definitions on success, or the failure code.
    def thing_def_list(self, offset = False, limit = False):
        """Acquire the list of Thing Definitions."""
        params = {}
        if offset != False:
            params["offset"] = offset
        if limit != False:
            params["limit"] = limit
        result = self.execute("thing_def.list", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]["result"]
        else:
            return self.response["data"]["success"]


    # thing.find : This command is used to find and return a thing.
    # @param     string    thing_key   Identifies the thing.
    # @return    mixed     Returns the array of the selected thing on success, or the failure code.
    def thing_find(self, thing_key):
        """This command is used to find and return a thing."""
        params = { "key" : thing_key }
        result = self.execute("thing.find", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # thing.list : This command is used to find and return a list of things.
    # @param     int       offset    The starting list offset, used for pagination. Defaults to 0 if not specified.
    # @param     int       limit     Limits the number of results returned. Defaults to the maximum configured size.
    # @param     array     show      An array of field names of the data columns to return.
    # @param     string    sort      A string indicated the direction ("+" for ascending, "-" for descending) and column to sort the results by. To sort by the key descending, use "-key". Defaults to "+name".
    # @param     array     tags      If specified, the command will only return things that have all tags in this parameter.
    # @param     array     keys      If specified, the command will only return things that have the keys specified in this parameter.
    # @return    mixed     Returns the dict of things on success, or the failure code.
    def thing_list(self, offset = False, limit = False, show = False,
                  sort = False, tags = False, keys = False):
        """This command is used to find and return a list of things."""
        params = {}
        if offset != False:
            params["offset"] = offset
        if limit != False:
            params["limit"] = limit
        if show != False:
            params["show"] = show
        if sort != False:
            params["sort"] = sort
        if tags != False and type(tags) is list:
            params["tags"] = tags
        if keys != False and type(keys) is list:
            params["keys"] = keys
        result = self.execute("thing.list", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]["result"]
        else:
            return self.response["data"]["success"]


    # twilio.sms.send : Send an SMS message to a phone number.
    # @param     string    smsTo      The recipient's phone number, or a comma separated string of phone numbers.
    # @param     string    smsBody    The body of the SMS message.
    # @param     mixed     smsFrom    The sender's phone number.
    # @return    bool      If the command executes successfully.
    def twilio_sms_send(self, sms_to, sms_body, sms_from = False):
        """This command is used to find and return a list of things."""
        params = { "to" : sms_to, "body" : sms_body }
        if sms_from != False and len(sms_from) > 0:
            params["from"] = sms_from
        result = self.execute("twilio.sms.send", params)
        return (result == True and self.response["data"]["success"] == True)


    # user.find : This command is used to retrieve a user by email address.
    # @param     string    email_address    The email address of the user.
    # @return    mixed     Returns the dict of the user on success, or the failure code.
    def user_find(self, email_address):
        """This command is used to find and return a list of things."""
        params = { "emailAddress" : email_address }
        result = self.execute("user.find", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]
        else:
            return self.response["data"]["success"]


    # user.list : This command is used to return a list of users.
    # @param     int      offset    The starting list offset, used for pagination, defaults to 0 if not specified.
    # @param     int      limit     Limits the number of results returned. Defaults to the maximum configured size.
    # @return    mixed    Returns an array of users on success, or the failure code.
    def user_list(self, offset = False, limit = False):
        """This command is used to find and return a list of things."""
        params = {}
        if offset != False:
            params["offset"] = offset
        if limit != False:
            params["limit"] = limit
        result = self.execute("user.list", params)
        if result == True and self.response["data"]["success"] == True:
            return self.response["data"]["params"]["result"]
        else:
            return self.response["data"]["success"]
