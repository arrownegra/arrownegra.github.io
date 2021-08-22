'''
	Copyright (C) 2014-2016 ddurdle

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading
import re
import urllib
import sys
import constants
import xbmc, xbmcgui

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	"""Handle requests in a separate thread."""

class MyHTTPServer(ThreadingMixIn, HTTPServer):

	def run(self):

		try:
			self.serve_forever()
		except KeyboardInterrupt:
			pass
		finally:
			# Clean-up server (close socket, etc.)
			self.server_close()

	def __init__(self, *args, **kw):
		HTTPServer.__init__(self, *args, **kw)
		self.ready = True

	def setFile(self, playbackURL, chunksize, playbackFile, response, fileSize, url, service):
		self.playbackURL = playbackURL
		self.chunksize = chunksize
		self.playbackFile = playbackFile
		self.response = response
		self.fileSize = fileSize
		self.url = url
		self.service = service
		self.ready = True
		self.state = 0
		self.lock = 0

	def setURL(self, playbackURL):
		self.playbackURL = playbackURL

	def setAccount(self, service, domain):
		self.service = service
		self.domain = domain
		self.playbackURL = ''
		self.crypto = False
		self.ready = True

	def setDetails(self, plugin_handle, PLUGIN_NAME, PLUGIN_URL, addon, user_agent, settings):
		self.plugin_handle = plugin_handle
		self.PLUGIN_NAME = PLUGIN_NAME
		self.PLUGIN_URL = PLUGIN_URL
		self.addon = addon
		self.user_agent = user_agent
		self.settings = settings
		#self.domain = domain
		self.playbackURL = ''
		self.crypto = False
		self.ready = True

class myStreamer(BaseHTTPRequestHandler):

	#Handler for the GET requests
	def do_POST(self):
		# debug - print headers in log
		headers = str(self.headers)
		print(headers)

		# passed a kill signal?
		if self.path == '/kill':
			self.server.ready = False
			return

		elif self.path == '/crypto_playurl':
			content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
			post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself

			for r in re.finditer('instance\=([^\&]+)\&url\=([^\|]+)', post_data, re.DOTALL):
				instanceName = r.group(1)
				url = r.group(2)
				drive_stream = ''
				xbmc.log("drive_stream = " + drive_stream + "\n")
				xbmc.log("url = " + url + "\n")
				cloudservice2 = constants.cloudservice2
				self.server.service = cloudservice2(self.server.plugin_handle, self.server.PLUGIN_URL, self.server.addon, instanceName, self.server.user_agent, self.server.settings)

				self.server.crypto = True
				self.server.playbackURL = url
				self.server.drive_stream = drive_stream

			self.send_response(200)
			self.end_headers()

		# redirect url to output
		elif self.path == '/enroll?default=false':
			content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
			post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
			self.send_response(200)
			self.end_headers()

			for r in re.finditer('client_id=([^&]+)&client_secret=([^&]+)', post_data, re.DOTALL):
				client_id = r.group(1)
				client_secret = r.group(2)
				data = '''
				<html>
				<head>
				<meta name="viewport" content="width=device-width, initial-scale=1">
				<style>
				.text {
								width: 300px;
								margin: 20 auto;
				}
				.container {
								position: absolute;
								top: 50%%;
								left: 50%%;
								-moz-transform: translateX(-50%%) translateY(-50%%);
								-webkit-transform: translateX(-50%%) translateY(-50%%);
								transform: translateX(-50%%) translateY(-50%%);
								background-color: 080808;
								border: 1px solid black;
								height: 200px;
								width: 300px;
								background-color: #0F0F0F;
								box-shadow: 5px 10px;
				}
				.inner {
								position: absolute;
								top: 50%%;
								left: 50%%;
								-moz-transform: translateX(-50%%) translateY(-50%%);
								-webkit-transform: translateX(-50%%) translateY(-50%%);
								transform: translateX(-50%%) translateY(-50%%);
				}
				.input {
								width: 200px;
								height: 26px;
								border: 0.6px solid black;
								background-color: #2E2E2E;
				}
				.button {
								width: 200px;
								height: 26px;
								margin-top: 20px;
								border: 0.6px solid black;
								background-color: #1D1D1D;
								margin-top: 21px;
				}
				a:link {
								color: white;
								text-decoration: none;
								font-family: Arial
				}
				a:hover {
								text-decoration: underline;
				}
				a:visited {
								color: white;
				}
				body {
								background-color: #080808;
				}
				</style>
				</head>
				<body>
				<a href="https://accounts.google.com/o/oauth2/auth?scope=https://www.googleapis.com/auth/drive&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&client_id=%s" target="_blank">
				<div class="text">
				Click here and paste the code in the form below and then enter an account name.
				</div>
				</a>
				<div class="container">
				<form action="/enroll" method="post">
				<div class="inner">
				<input div class="input" style="color:white" type="text" name="account" placeholder="Account name">
				<br/>
				<br/>
				<input div class="input" style="color:white" type="text" name="code" placeholder="Google code">
				<br/>
				<input div class="button" style="color:white" type="submit" value="Submit">
				<input hidden div class="input" style="color:white" type="text" name="client_id" value="%s" placeholder="Client ID">
				<input hidden div class="input" style="color:white" type="text" name="client_secret" value="%s" placeholder="Client secret">
				</div>
				</div>
				</form>
				</div>
				</body>
				</html>''' % (client_id, client_id, client_secret)
				self.wfile.write(data.encode('utf-8') )

		# redirect url to output
		elif self.path == '/enroll':
			content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
			post_data = self.rfile.read(content_length).decode('utf-8') # <--- Gets the data itself
			self.send_response(200)
			self.end_headers()

			for r in re.finditer('account=([^&]+)&code=([^&]+)&client_id=([^&]+)&client_secret=([^&]+)', post_data, re.DOTALL):
				account = r.group(1)
				client_id = r.group(3)
				client_secret = r.group(4)
				code = r.group(2)
				code = code.replace('%2F', '/')

				#self.wfile.write(b'<html><body>account = '+ str(account) + " " + str(client_id) + " " + str(client_secret) + " " + str(code) )

				count = 1
				loop = True

				while loop:
					instanceName = self.server.PLUGIN_NAME + str(count)

					try:
						username = self.server.settings.getSetting(instanceName + '_username')
					except:
						username = ''

					if username == account or username == '':
						self.server.addon.setSetting(instanceName + '_username', str(account) )
						self.server.addon.setSetting(instanceName + '_code', str(code) )
						self.server.addon.setSetting(instanceName + '_client_id', str(client_id) )
						self.server.addon.setSetting(instanceName + '_client_secret', str(client_secret) )

						if count > self.server.addon.getSettingInt("account_amount"):
							self.server.addon.setSetting("account_amount", str(count) )

						loop = False

					count += 1

				url = 'https://accounts.google.com/o/oauth2/token'
				header = {'User-Agent' : self.server.user_agent, 'Content-Type' : 'application/x-www-form-urlencoded'}

				data = 'code=' + str(code) + '&client_id=' + str(client_id) + '&client_secret=' + str(client_secret) + '&redirect_uri=urn:ietf:wg:oauth:2.0:oob&grant_type=authorization_code'
				req = urllib.request.Request(url, data.encode('utf-8'), header)

				# try login
				try:
					response = urllib.request.urlopen(req)
				except urllib.error.URLError as e:
					self.send_response(200)
					self.end_headers()
					self.wfile.write(str(e).encode('utf-8') )
					return

				response_data = response.read().decode('utf-8')
				response.close()

				# retrieve authorization token
				for r in re.finditer('\"access_token\"\s?\:\s?\"([^\"]+)\".+?' + '\"refresh_token\"\s?\:\s?\"([^\"]+)\".+?', response_data, re.DOTALL):
					accessToken, refreshToken = r.groups()
					self.server.addon.setSetting(instanceName + '_auth_access_token', str(accessToken) )
					self.server.addon.setSetting(instanceName + '_auth_refresh_token', str(refreshToken) )
					self.wfile.write(b'Successfully enrolled account.')
					self.server.ready = False

				for r in re.finditer('\"error_description\"\s?\:\s?\"([^\"]+)\"', response_data, re.DOTALL):
					errorMessage = r.group(1)
					self.wfile.write(errorMessage.encode('utf-8') )

				return

	def do_HEAD(self):
		# debug - print headers in log
		headers = str(self.headers)
		print(headers)

		# passed a kill signal?
		if self.path == '/kill':
			self.server.ready = False
			return

		# redirect url to output
		elif self.path == '/play':
			url = self.server.playbackURL
			xbmc.log('HEAD ' + url + "\n")
			req = urllib.request.Request(url, None, self.server.service.getHeadersList() )
			req.get_method = lambda : 'HEAD'

			try:
				response = urllib.request.urlopen(req)
			except urllib.error.URLError as e:

				if e.code == 404:
					xbmcgui.Dialog().ok(self.server.addon.getLocalizedString(30003), self.server.addon.getLocalizedString(30209) )
					return
				elif e.code == 401 or e.code == 403 or e.code == 429:
					xbmc.log("ERROR\n" + self.server.service.getHeadersEncoded() )
					self.server.service.refreshToken()
					req = urllib.request.Request(url, None, self.server.service.getHeadersList() )
					req.get_method = lambda : 'HEAD'

					try:
						response = urllib.request.urlopen(req)
					except:
						xbmc.log("STILL ERROR\n" + self.server.service.getHeadersEncoded() )

						if e.code == 401:
							xbmcgui.Dialog().ok(self.server.addon.getLocalizedString(30003), self.server.addon.getLocalizedString(30018) )
							return
						elif e.code == 403 or e.code == 429:

							if self.server.addon.getSetting("fallback"):
								fallbackAccounts = self.server.addon.getSetting("fallback_accounts").split(',')
								defaultAccount = self.server.addon.getSetting("default_account")
								accountChange = False

								for fallbackAccount in fallbackAccounts:

									username = self.server.addon.getSetting("gdrive%s_username" % fallbackAccount)

									if not username:
										fallbackAccounts.remove(fallbackAccount)
										continue

									try:
										cloudservice2 = constants.cloudservice2
										self.server.service = cloudservice2(self.server.plugin_handle, self.server.PLUGIN_URL, self.server.addon, "gdrive" + fallbackAccount, self.server.user_agent, self.server.settings)
										self.server.service.refreshToken()

										req = urllib.request.Request(url, None, self.server.service.getHeadersList() )
										req.get_method = lambda : 'HEAD'
										response = urllib.request.urlopen(req)

										if not defaultAccount in fallbackAccounts:
											fallbackAccounts.append(defaultAccount)

										fallbackAccounts.remove(fallbackAccount)
										self.server.addon.setSetting("default_account", fallbackAccount)
										self.server.addon.setSetting("default_account_ui", username)
										accountChange = True
										xbmcgui.Dialog().notification(self.server.addon.getLocalizedString(30003) + ': ' + self.server.addon.getLocalizedString(30006), self.server.addon.getLocalizedString(30007) )
										break

									except:
										continue

								self.server.addon.setSetting("fallback_accounts", ','.join(fallbackAccounts) )
								self.server.addon.setSetting('fallback_accounts_ui', ', '.join(self.server.addon.getSetting("gdrive%s_username" % x) for x in fallbackAccounts) )

								if not accountChange:
									xbmcgui.Dialog().ok(self.server.addon.getLocalizedString(30003) + ': ' + self.server.addon.getLocalizedString(30006), self.server.addon.getLocalizedString(30009) )
									return

							else:
								xbmcgui.Dialog().ok(self.server.addon.getLocalizedString(30003) + ': ' + self.server.addon.getLocalizedString(30006), self.server.addon.getLocalizedString(30009) )
								return

						else:
							return

				else:
					return

			self.send_response(200)
			self.send_header('Content-Type', response.info().get('Content-Type') )
			self.send_header('Content-Length', response.info().get('Content-Length') )
			self.send_header('Cache-Control', response.info().get('Cache-Control') )
			self.send_header('Date', response.info().get('Date') )
			self.send_header('Content-type', 'video/mp4')
			self.send_header('Accept-Ranges', 'bytes')

			#self.send_header('ETag', response.info().get('ETag') )
			#self.send_header('Server', response.info().get('Server') )
			self.end_headers()

			## may want to add more granular control over chunk fetches
			#self.wfile.write(response.read() )

			response.close()
			xbmc.log("DONE")
			self.server.length = response.info().get('Content-Length')

	#Handler for the GET requests
	def do_GET(self):
		# debug - print headers in log
		headers = str(self.headers)
		print(headers)

		start = ''
		end = ''
		startOffset = 0

		for r in re.finditer('Range\:\s+bytes\=(\d+)\-', headers, re.DOTALL):
			start = int(r.group(1) )
			break

		for r in re.finditer('Range\:\s+bytes\=\d+\-(\d+)', headers, re.DOTALL):
			end = int(r.group(1) )
			break

		# passed a kill signal?
		if self.path == '/kill':
			self.server.ready = False
			return

		# redirect url to output
		elif self.path == '/play':

			if (self.server.crypto and start != '' and start > 16 and end == ''):
				#start = start - (16 - (end % 16) )
				xbmc.log("START = " + str(start) )
				startOffset = 16 - ( (int(self.server.length) - start) % 16) + 8

#			 if (self.server.crypto and start == 23474184):
				#start = start - (16 - (end % 16) )
#				start = 23474184 - 8

			url = self.server.playbackURL
			xbmc.log('GET ' + url + "\n" + self.server.service.getHeadersEncoded() + "\n")

			if start == '':
				req = urllib.request.Request(url, None, self.server.service.getHeadersList() )
			else:
				req = urllib.request.Request(url, None, self.server.service.getHeadersList(additionalHeader='Range', additionalValue='bytes=' + str(start- startOffset) + '-' + str(end) ) )

			try:
				response = urllib.request.urlopen(req)
			except urllib.error.URLError as e:

				if e.code == 403 or e.code == 401:
					xbmc.log("ERROR\n" + self.server.service.getHeadersEncoded() )
					self.server.service.refreshToken()
					req = urllib.request.Request(url, None, self.server.service.getHeadersList() )

					try:
						response = urllib.request.urlopen(req)
					except:
						xbmc.log("STILL ERROR\n" + self.server.service.getHeadersEncoded() )
						return
				else:
					return

			if start == '':
				self.send_response(200)
				self.send_header('Content-Length', response.info().get('Content-Length') )
			else:
				self.send_response(206)
				self.send_header('Content-Length', str(int(response.info().get('Content-Length') ) - startOffset) )
				#self.send_header('Content-Range', 'bytes ' + str(start) + '-' + str(end) )

				if end == '':
					self.send_header('Content-Range', 'bytes ' + str(start) + '-' + str(int(self.server.length) - 1) + '/' + str(int(self.server.length) ) )
				else:
					self.send_header('Content-Range', 'bytes ' + str(start) + '-' + str(end) + '/' + str(int(self.server.length) ) )

				#self.send_header('Content-Range', response.info().get('Content-Range') )
				xbmc.log('Content-Range!!!' + str(start) + '-' + str(int(self.server.length) - 1) + '/' + str(int(self.server.length) ) + "\n")

			xbmc.log(str(response.info() ) + "\n")
			self.send_header('Content-Type', response.info().get('Content-Type') )

#			 self.send_header('Content-Length', response.info().get('Content-Length') )
			self.send_header('Cache-Control', response.info().get('Cache-Control') )
			self.send_header('Date', response.info().get('Date') )
			self.send_header('Content-type', 'video/mp4')
			self.send_header('Accept-Ranges', 'bytes')

			self.end_headers()

			## may want to add more granular control over chunk fetches
			#self.wfile.write(response.read() )

			if (self.server.crypto):
				from resources.lib import encryption
				decrypt = encryption.encryption(self.server.addon.getSetting("crypto_salt"), self.server.addon.getSetting("crypto_password") )

				CHUNK = 16 * 1024
				decrypt.decryptStreamChunkOld(response, self.wfile, startOffset=startOffset)

			response.close()

		# redirect url to output
		elif self.path == '/enroll':
			self.send_response(200)
			self.end_headers()
			self.wfile.write(b'''
			<html>
			<head>
			<meta name="viewport" content="width=device-width, initial-scale=1">
			<style>
			.container {
							position: absolute;
							top: 50%;
							left: 50%;
							-moz-transform: translateX(-50%) translateY(-50%);
							-webkit-transform: translateX(-50%) translateY(-50%);
							transform: translateX(-50%) translateY(-50%);
							background-color: 080808;
							border: 1px solid black;
							height: 200px;
							width: 300px;
							background-color: #0F0F0F;
							box-shadow: 5px 10px;
			}
			.inner {
							position: absolute;
							top: 50%;
							left: 50%;
							-moz-transform: translateX(-50%) translateY(-50%);
							-webkit-transform: translateX(-50%) translateY(-50%);
							transform: translateX(-50%) translateY(-50%);
			}
			.input {
							width: 200px;
							height: 26px;
							border: 0.6px solid black;
							background-color: #2E2E2E;
			}
			.button {
							width: 200px;
							height: 26px;
							border: 0.6px solid black;
							background-color: #1D1D1D;
							margin-top: 21px;

			}
			body {
							background-color: #080808;
			}
			</style>
			</head>
			<body>
			<div class="container">
			<form action="/enroll?default=false" method="post">
			<div class="inner">
			<input div class="input" style="color:white" type="text" name="client_id" placeholder="Client ID">
			<br/>
			<br/>
			<input div class="input" style="color:white" type="text" name="client_secret" placeholder="Client Secret">
			<br/>
			<input div class="button" style="color:white" type="submit" value="Submit">
			</div>
			</div>
			</form>
			</body>
			</html>''')
			return