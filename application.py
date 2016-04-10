#!/usr/bin/env python

import os
import logging
import json

import requests
from bottle import route, request, response, redirect, hook, error, default_app, view, static_file, template, HTTPError

@error('404')
@error('403')
def returnError(code, msg, contentType="text/plain"):
    response.status = int(code)
    response.content_type = contentType
    return template('error')

@hook('before_request')
def determine_content_type():
    if request.headers.get('Accept') == "application/json":
        response.content_type = 'application/json'    
    elif request.headers.get('Accept') == "text/plain":
        response.content_type = 'text/plain'

@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='views/static')

@route('/version')
def return_version():
    try:
        dirname, filename = os.path.split(os.path.abspath(__file__))
        del filename
        f = open(os.getenv('VERSION_PATH', dirname + '/.git/refs/heads/master'), 'r')
        content = f.read()
        response.content_type = 'text/plain'
        return content
    except:
        return "Unable to open version file."

@route('/<record>')
@route('/<record>/<type>')
@route('/<record>/<type>.<ext>')
def loadRecord(record="", type="", ext="html"):
    
    if record == "" or type == "":
        return returnError(404, "Not Found", "text/html")
    
    if not ext in ["html","txt", "text","json"]:
        ext = "html"
    
    if ext == "json":
        response.content_type = 'application/json'    
    elif ext in ["txt","text"]:
        response.content_type = 'text/plain'

    if not type.upper() in appRecords:
        return returnError(404, "Not Found", "text/html")
    
    # We make a request to get information
    data = requests.get(appLookup + "/" + record + "/" + type.upper())

    recSet = []   
    try:
        for rec in data.json()['answer']:
            recSet.append(rec['rdata'])
    except:
        recSet.append("Unable to identify any records with type: " + type)
    
    content = {
        'name': record,
        'type': type.upper(),
        'records': recSet,
        'recTypes': appRecords
    }

    if ext == "json" or response.content_type == 'application/json' :
        del content['recTypes']
        jsonContent = {
            "results": content
        }
        return json.dumps(jsonContent)
    elif ext in ["txt","text"] or response.content_type == "text/plain":
        return "\r\n".join(recSet)
    else:
        return template('rec', content)

@route('/', method="POST")
def postIndex():
    
    try:
        recordName = request.forms.get('recordName')
        recordType = request.forms.get('recordType')
    except AttributeError:
        return returnError(404, "Not Found", "text/html")
    
    # Handle someone trying to modify the <select>
    if not recordType == "Type" and not recordType in appRecords:
        return returnError(404, "Not Found", "text/html")
    
    # Now empty record checking
    if recordName == "" or recordType == "Type":
        return returnError(404, "Not Found", "text/html")
    
    return redirect("/" + recordName + "/" + recordType)

@route('/')
def index():
    content = {
        'recTypes': appRecords
    }
    return template("home", content)

if __name__ == '__main__':
    
    app = default_app()
    
    appReload = bool(os.getenv('APP_RELOAD', False))
    appLookup = os.getenv('APP_LOOKUP', "http://dig.mgall.me/8.8.8.8:53")
    appRecords = ["A", "AAAA", "CNAME", "DS", "DNSKEY", "MX", "NS", "NSEC", "NSEC3", "RRSIG", "SOA", "TXT"]

    serverHost = os.getenv('IP', 'localhost')
    serverPort = os.getenv('PORT', '5000')

    # Now we're ready, so start the server
    # Instantiate the logger
    log = logging.getLogger('log')
    console = logging.StreamHandler()
    log.setLevel(logging.INFO)
    log.addHandler(console)
    
    # Now we're ready, so start the server
    try:
        log.info("Successfully started application server")
        app.run(host=serverHost, port=serverPort, reloader=bool(appReload))
    except:
        log.error("Failed to start application server")