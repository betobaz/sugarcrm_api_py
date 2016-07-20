import requests
import json
import urllib
import pprint
import sys
from os.path import basename
from requests_toolbelt import MultipartEncoder
import unicodedata

from django.core.exceptions import ObjectDoesNotExist

class SugarCRMAPI(object):

	access_token = None
	refresh_token = None
	REST10 =  "rest/v10"
	HTTP_METHODS = {
		"post": requests.post,
		"put": requests.put,
		"get": requests.get,
		"delete": requests.delete
	}
	url = None

	def __init__(self, url, client_id, client_secret):
		self.url = url + self.REST10
		self.client_id = client_id
		self.client_secret = client_secret

	def set_token(self, access_token):
		self.access_token = access_token

	def set_refresh_token(self, refresh_token):
		self.refresh_token = refresh_token

	def oauth2_token(self, user_name, password):
		
		payload = {
			"grant_type" : "password",
		    "username" : user_name,
		    "password" : password,
		    "client_id" : self.client_id,
		    "client_secret" : self.client_secret,
		    "platform": "cti",
		}
		url = self.url + '/oauth2/token'
		headers = {
			"Content-Type": "application/json"
		}
		#import ipdb; ipdb.set_trace()
		response = requests.post( url, data=json.dumps(payload), headers = headers)		
		result = {}
		if response.status_code == 200:
			result['response_dic'] = json.loads(response.text)
			self.access_token = result['response_dic']['access_token']
			self.refresh_token = result['response_dic']['refresh_token']
			#self.user.save()	
		result['status_code'] = response.status_code
		return  result

	def refresh(self):

		payload = {
			"grant_type" : "refresh_token",
		    "client_id" : self.client_id,
		    "client_secret" : self.client_secret,
			"refresh_token": self.refresh_token,
			"platform": "cti",
		}
		url = self.url + '/oauth2/token'
		headers = {
			"Content-Type": "application/json"
		}
		response = requests.post( url, data=json.dumps(payload), headers = headers)
		result = None
		#pprint.pprint(response.text)
		if response.status_code == 200:
			result = json.loads(response.text)
		return  result

	def save(self, module, data):
		headers = self.get_headers()
		url = self.url + '/' + module
		response = requests.post( url, json.dumps(data), headers = headers)
		if response.status_code == 200:
			return json.loads(response.text)
		elif response.status_code == 401:
			return None

	def call(self, method, url, data = None):		
		headers = self.get_headers()				
		url_full = "{url}/{route}".format(url=self.url,route=url)
		response = None
		# import ipdb; ipdb.set_trace()

		if method == "get" or method == "delete":
			response = self.HTTP_METHODS[method](url_full,params = data, headers = headers)
		else:
			response = self.HTTP_METHODS[method](url_full, json.dumps(data), headers = headers)
		#print("call::response")
		#print(response.text)
		if response.status_code == 200:
			#pprint.pprint(response.text)
			return json.loads(response.text)
		elif response.status_code == 401:
			#pprint.pprint("El usuario con llave {key} no tiene acceso".format(key=self.user.key))
			refresh_result = self.refresh()
			#pprint.pprint(refresh_result)
			if refresh_result:
				self.access_token = refresh_result['access_token']
				self.refresh_token = refresh_result['refresh_token']
				#pprint.pprint(response.status_code)
				return self.call(method, url, data)
			return None		

	def get_entries(self, module, filterexp = "", max_num = 20, offset=0,fields="",order_by="",q="",deleted=""):
		headers = self.get_headers()
		url = "%s/%s"%(self.url,module)
		data = {
			"filter" :filterexp,
			"max_num" :max_num,
			"offset" :offset,
			"fields" :fields,
			"order_by" :order_by,
			"q" :q,
			"deleted" :deleted,
		}
		response = requests.get(url,params = data, headers = headers)
		if response.status_code == 200:
			return json.loads(response.text)
		elif response.status_code == 401:
			return None


	def search(self, q="",max_num=20,offset=0,fields="",order_by="",favorites="",my_items=""):
		headers = self.get_headers()
		url = "%s/search"%(self.url)
		data = {
			"q":q,
			"max_num" : max_num,
			"offset" : offset,
			"fields" : fields,
			"order_by" : order_by,
			"favorites" : favorites,
			"my_items" : my_items,
		}
		response = requests.get(url,params = data, headers = headers)
		if response.status_code == 200:
			return json.loads(response.text)
		elif response.status_code == 401:
			return None

	def create_link(self, module, id, linkName, linkId):
		headers = self.get_headers()
		url = "%s/%s/%s/link/%s/%s"%(self.url,module,id,linkName,linkId)
		response = requests.post( url, headers = headers)
		if response.status_code == 200:
			return json.loads(response.text)
		elif response.status_code == 401:
			return None

	def get_links(self, module, id, linkName):
		headers = self.get_headers()
		url = "%s/%s/%s/link/%s"%(self.url,module,id,linkName)
		response = requests.get( url, headers = headers)
		if response.status_code == 200:
			return json.loads(response.text)
		elif response.status_code == 401:
			return None

	def get_headers(self):
		if not(self.access_token):
			raise ObjectDoesNotExist
		headers = {
			"Content-Type": "application/json",
			"OAuth-Token": str(self.access_token),
		}
		return headers

	def upload(self, url, file_content, content_type, field_name):
		#headers = self.get_headers()				
		url = "{url}/{route}".format(url=self.url,route=url)
		response = None
		file_name = basename(file_content.name).decode('unicode-escape')
		filename = unicodedata.normalize('NFKD',file_name).encode('ASCII', 'ignore')
		# m = MultipartEncoder(
		# fields={
		# 	field_name: (filename, file_content.read(), content_type)
		# })
		fields = {}
		fields[field_name] = (filename, file_content.read(), content_type)
		m = MultipartEncoder(fields=fields)
		print url
		print content_type

		response = self.HTTP_METHODS['post'](url,data=m,headers={'Content-Type': m.content_type})
		print response.text
		if response.status_code == 200:
			return json.loads(response.text)
		elif response.status_code == 401:
			refresh_result = self.refresh()
			if refresh_result:
				self.access_token = refresh_result['access_token']
				self.refresh_token = refresh_result['refresh_token']
				return self.upload(url, file_content, content_type, field_name)
			return None
