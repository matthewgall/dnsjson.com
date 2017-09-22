#!/usr/bin/env python3

import os, logging, argparse, json, datetime
import requests
import dns.resolver
from bottle import route, request, response, redirect, hook, error, default_app, view, static_file, template

def set_content_type(fn):
	def _return_json(*args, **kwargs):
		response.headers['Content-Type'] = 'application/json'
		if request.method != 'OPTIONS':
			return fn(*args, **kwargs)
	return _return_json

def enable_cors(fn):
	def _enable_cors(*args, **kwargs):
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
		response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

		if request.method != 'OPTIONS':
			return fn(*args, **kwargs)
	return _enable_cors

def resolveDomain(domain, recordType, dnsAddr):
	try:
		records = []
		
		resolver = dns.resolver.Resolver()
		resolver.nameservers = dnsAddr.split(',')
		
		if recordType in args.records.split(','):
			lookup = resolver.query(domain, recordType)
			for data in lookup:
				if recordType in ['A', 'AAAA']:
					records.append(data.address)
				elif recordType in ['TXT']:
					for rec in data.strings:
						records.append(rec.decode("utf-8").replace('"', '').strip())
				else:
					records.append(str(data).replace('"', '').strip())
		return records
	except dns.resolver.NXDOMAIN:
		return records
	except dns.resolver.NoAnswer:
		return records
	except dns.exception.Timeout:
		return records
	except dns.resolver.NoNameservers:
		return records
		
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

@hook('after_request')
def log_to_console():
	log.info("{} {} {}".format(
		datetime.datetime.now(),
		response.status_code,
		request.url
	))

@route('/static/<filepath:path>')
def server_static(filepath):
	return static_file(filepath, root='views/static')

@route('/servers')
def return_servers():
	try:
		response.content_type = 'text/plain'
		return "\r\n".join(args.resolver.split(","))
	except:
		return "Unable to open servers file."
		
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
@enable_cors
def loadRecord(record="", type="", ext="html"):
	try:
		if record == "" or type == "":
			raise ValueError
		if not type.upper() in args.records.split(','):
			raise ValueError
		if not ext in ["html","txt", "text","json"]:
			ext = "html"
		if ext == "json":
			response.content_type = 'application/json'    
		elif ext in ["txt","text"]:
			response.content_type = 'text/plain'
	except ValueError:
		return returnError(404, "Not Found", "text/html")

	# We make a request to get information
	data = resolveDomain(record, type.upper(), args.resolver)
	
	content = {
		'name': record,
		'type': type.upper(),
		'records': data,
		'recTypes': args.records.split(',')
	}

	if ext == "json" or response.content_type == 'application/json' :
		del content['recTypes']
		
		jsonContent = {
			"results": content
		}
			
		return json.dumps(jsonContent)
	elif ext in ["txt","text"] or response.content_type == "text/plain":
		return "\r\n".join(data)
	else:
		return template('rec', content)

@route('/', method="POST")
def postIndex():
	
	try:
		recordName = request.forms.get('recordName')
		recordType = request.forms.get('recordType')

		if not recordType == "Type" and not recordType in args.records.split(','):
			raise ValueError
		if recordName == "" or recordType == "Type":
			raise ValueError
		return redirect("/{}/{}".format(recordName, recordType))
	except ValueError:
		return returnError(404, "Not Found", "text/html")
	except AttributeError:
		return returnError(404, "Not Found", "text/html")

@route('/')
def index():
	content = {
		'recTypes': args.records.split(',')
	}
	return template("home", content)

if __name__ == '__main__':

	parser = argparse.ArgumentParser()

	# Server settings
	parser.add_argument("-i", "--host", default=os.getenv('IP', '127.0.0.1'), help="server ip")
	parser.add_argument("-p", "--port", default=os.getenv('PORT', 5000), help="server port")

	# Redis settings
	parser.add_argument("--redis-host", default=os.getenv('REDIS_HOST', 'redis'), help="redis hostname")
	parser.add_argument("--redis-port", default=os.getenv('REDIS_PORT', 6379), help="redis port")
	parser.add_argument("--redis-pw", default=os.getenv('REDIS_PW', ''), help="redis password")
	parser.add_argument("--redis-ttl", default=os.getenv('REDIS_TTL', 60), help="redis time to cache records")

	# Application settings
	parser.add_argument("--records", default=os.getenv('APP_RECORDS', "A,AAAA,CNAME,DS,DNSKEY,MX,NS,NSEC,NSEC3,RRSIG,SOA,TXT"), help="supported records")
	parser.add_argument("--resolver", default=os.getenv('APP_RESOLVER', '8.8.8.8'), help="resolver address")

	# Verbose mode
	parser.add_argument("--verbose", "-v", help="increase output verbosity", action="store_true")
	args = parser.parse_args()

	if args.verbose:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)
	log = logging.getLogger(__name__)

	try:
		app = default_app()
		app.run(host=args.host, port=args.port, server='tornado')
	except:
		log.error("Unable to start server on {}:{}".format(args.host, args.port))