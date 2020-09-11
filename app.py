#!/usr/bin/env python3

import os, logging, argparse, json, datetime
import requests
import dns.resolver
from bottle import route, request, response, redirect, hook, error, default_app, view, static_file, template

def set_content_type(fn):
	def _return_type(*args, **kwargs):
		if request.headers.get('Accept') == "application/json":
			response.headers['Content-Type'] = 'application/json'
		if request.headers.get('Accept') == "text/plain":
			response.headers['Content-Type'] = 'text/plain'
		if request.method != 'OPTIONS':
			return fn(*args, **kwargs)
	return _return_type

def enable_cors(fn):
	def _enable_cors(*args, **kwargs):
		response.headers['Access-Control-Allow-Origin'] = '*'
		response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
		response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

		if request.method != 'OPTIONS':
			return fn(*args, **kwargs)
	return _enable_cors

def resolveDomain(domain, recordType, args):
	records = []

	if args.doh:
		try:
			payload = {
				'name': domain,
				'type': recordType
			}
			data = requests.get("{}".format(args.resolver), params=payload)
			for rec in data.json()['Answer']:
				records.append(rec['data'])
		except:
			return records
		return records
	else:
		try:
			resolver = dns.resolver.Resolver()
			resolver.nameservers = args.resolver.split(',')
			
			if recordType in args.records.split(','):
				lookup = resolver.resolve(domain, recordType)
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

@route('/static/<filepath:path>')
def static(filepath):
	return static_file(filepath, root='views/static')

@route('/servers')
def servers():
	try:
		response.content_type = 'text/plain'
		return "\r\n".join(args.resolver.split(","))
	except:
		return "Unable to open servers file."
		
@route('/version')
def version():
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
def route_redirect(record):
	return redirect("/{}/A".format(record))

@route('/<record>/<type>')
@route('/<record>/<type>.<ext>')
@set_content_type
@enable_cors
def loadRecord(record, type='A', ext='html'):
	try:
		if record == "":
			raise ValueError
		if not ext in ["html","txt", "text", "json"]:
			raise ValueError
		if not type.upper() in args.records.split(','):
			raise ValueError
	except ValueError:
		return returnError(404, "Not Found", "text/html")

	if ext in ["json"]:
		response.content_type = 'application/json'
	if ext in ["txt", "text"]:
		response.content_type = 'text/plain'

	# We make a request to get information
	data = resolveDomain(record, type.upper(), args)

	if response.content_type == 'application/json':
		return json.dumps({
			'results': {
				'name': record,
				'type': type.upper(),
				'records': data,
			}
		})
	elif response.content_type == "text/plain":
		return "\r\n".join(data)
	else:
		return template('rec', {
			'name': record,
			'type': type.upper(),
			'records': data,
			'recTypes': args.records.split(',')
		})

@route('/', ('GET', 'POST'))
def index():

	if request.method == "POST":
		recordName = request.forms.get('recordName', '')
		recordType = request.forms.get('recordType', '')

		if recordName != '' and recordType in args.records.split(','):
			return redirect("/{}/{}".format(recordName, recordType))
		else:
			return returnError(404, "We were not able to figure out what you were asking for", "text/html")

	return template("home", {
		'recTypes': args.records.split(',')
	})

if __name__ == '__main__':

	parser = argparse.ArgumentParser()

	# Server settings
	parser.add_argument("-i", "--host", default=os.getenv('HOST', '127.0.0.1'), help="server ip")
	parser.add_argument("-p", "--port", default=os.getenv('PORT', 5000), help="server port")

	# Redis settings
	parser.add_argument("--redis", default=os.getenv('REDIS', 'redis://localhost:6379/0'), help="redis connection string")

	# Application settings
	parser.add_argument("--doh", help="use DNS-over-HTTPS and treat --resolver as DNS-over-HTTPS capable (beta)", action="store_true")
	parser.add_argument("--records", default=os.getenv('RECORDS', "A,AAAA,CAA,CNAME,DS,DNSKEY,MX,NS,NSEC,NSEC3,RRSIG,SOA,TXT"), help="supported records")
	parser.add_argument("--resolver", default=os.getenv('RESOLVER', '8.8.8.8'), help="resolver address")

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