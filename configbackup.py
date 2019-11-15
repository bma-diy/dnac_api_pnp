import os
import http.client
import ssl
import json
import re
import datetime


def main():
	"""
	This script saves the config of all network devices and stores them in the DNAC/ directory.
	"""

	currentDT = datetime.datetime.now()
	date = currentDT.strftime("%Y-%m-%d_%H-%M")

	dnacip = "172.16.X.X"	
	dnacpw = "Basic YWRtaW46QzFzYzA="

	directoryPath = 'DNAC/'

	print(f"\nDNAC GETCONFIG API DEMO\nDNAC: {dnacip}\nConfigs will be saved in {directoryPath}\n")

	conn = http.client.HTTPSConnection(dnacip, context = ssl._create_unverified_context())

	headersx = get_authtoken(dnacpw, conn)

	get_config(headersx, conn, directoryPath, date)

def get_authtoken(dnacpw2, conn):
	"""Authentication API"""

	headers = {
		'content-type': "application/json",
		'authorization': dnacpw2	#authorization is Basic + 64bit encoding of user:password
		}
	
	conn.request("POST", "/dna/system/api/v1/auth/token", headers=headers)

	res = conn.getresponse()
	data = res.read()
	token = data.decode("utf-8")
	token = json.loads(token)

	headerstoken = {
		'content-type': "application/json",
		'x-auth-token': token["Token"]
		}

	return headerstoken

def get_config(headers2, conn, filePath, date2):

	conn.request("GET", "/dna/intent/api/v1/network-device/config", headers=headers2)

	res = conn.getresponse()
	data = res.read()
	data = data.decode("utf-8")
	config = json.loads(data)

	for config in config["response"]:
		#hostname = re.search('hostname (.)\n',config["runningConfig"]) 
		 
		hostname = re.search(' *hostname(?:(?!\\n).)*',config["runningConfig"]) 
		# re.search(' *hostname(?:(?!\\n).)*',config["response"][0]["runningConfig"]) 
		# a match here would confirm the device is a router/ switch

		if hostname: 	

			hostname = hostname.group(0).split()

			hostname = hostname[1]
			print(f"Hostname: {hostname}")

		else: 
			# if it's not a router/ switch it will be a wlc and will have a System Name instead.
			hostname = re.search('System Name\.+\s(.+)\\nSystem Location',config["runningConfig"])
			#testing: re.search('System Name\.+\s(.+)\\nSystem Location',config["response"][1]["runningConfig"])

			hostname = hostname.group(1)

			print(f"WLC: {hostname}")
		
		if not os.path.exists(filePath+hostname):
			print(f"making Directory... {filePath}{hostname}\n\n")
			
			os.makedirs('DNAC/'+hostname)
		
		file = open(filePath+""+hostname+"/"+hostname+""+date2+".txt","w") 
		file.write(config["runningConfig"]) 
		print(f"Created {filePath}{hostname}/{hostname}{date2}.txt\n")
		file.close()

main()