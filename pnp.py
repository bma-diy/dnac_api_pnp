import os
import http.client
import ssl
import json
import re
import datetime

def main():
	"""
	https://developer.cisco.com/docs/dna-center/#!cisco-dna-center-platform-overview/integration-api-westbound

	Prereq: Device is 'unclaimed'

	API Authentication, must be in following format: Basic base64encode(username:password)
		
	Example: DNAC GUI user/pw is admin/C1sc0, the base64encode of "admin:C1sc0" would be YWRtaW46QzFzYzA=

	"""

	dnacip = "172.16.X.X"	
	dnacpw = "Basic YWRtaW46QzFzYzA="	

	print(f"\nDNAC API Demo\nDNAC: {dnacip}\n")

	siteIn = input("Input Site: ").rstrip()	# Input site name.
	if siteIn == '':		# Alternatively, leave it blank and hit enter to use default site
		siteIn = 'Global/Cisco/Building 1'
		print(f"Site: {siteIn}\n")

	serialNum = input("Input Serial Number: ").rstrip()	# Input device serial number
	if serialNum == '':		# Alternatively, leave it blank and hit enter to use default SN
		serialNum = 'DEMO0000002'	#Example: DEMO0000002
		print(f"SN: {serialNum}\n")

	template_selected = input("Input Template to Use: ").rstrip()	
	if template_selected == '':		# Leave it blank and hit enter to use default template
		template_selected = 'Basic Config'	#"Example: Basic Config"
		print(f"Template: {template_selected}\n")

	print(f"\nAPI: Requesting site, device, and template info...\n")

	conn = http.client.HTTPSConnection(dnacip, context = ssl._create_unverified_context())

	headersx = get_authtoken(dnacpw, conn)
	id_site, name_site = get_site(siteIn, headersx, conn)
	id_device, sn_device, hostname_device, pid_device = get_devicelist(serialNum, headersx, conn)
	id_template, name_template = get_template(template_selected, headersx, conn)

	print(f"\n*Site Info*\n\tSite: {name_site} \n\tSite ID: {id_site}")
	print(f"\n*Device Info*\n\tHostname: {hostname_device} \n\tDevice PID: {pid_device} \n\tDevice SN: {sn_device} \n\tDevice ID: {id_device}")
	print(f"\n*Template Info*\n\tTemplate Name: {name_template} \n\tTemplate ID: {id_template}\n")

	print("\nClaiming Device...\n")

	configvariable = [
                        {
                            "key": "hostname",
                            "value": "9500-10"
                        },
                        {
                            "key": "loopbackaddress",
                            "value": "192.168.20.6"
                        },
                        {
                            "key": "linkIP",
                            "value": "192.168.16.14"
                        },
                        {
                            "key": "link",
                            "value": "TenGigabitEthernet1/0/7"
                        }
                    ]

	claimstatus = claim_device(id_site, id_device, id_template, headersx, conn, configvariable)
	if claimstatus == 'Device Claimed':
		print(f"\n*Claim Status*\n\t{claimstatus}\n\tDevice is now in 'planned' state.\n")
	else:
		print(f"\n*Claim Status*\n\t{claimstatus}\n")

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


def get_site(siteInput, headers2, conn):
	""" Get Site API - Returns the list of sites, matches siteNameHierarchy"""

	siteNameHierarchy = siteInput.replace(" ","%20")

	conn.request("GET", f"/dna/intent/api/v1/site?name={siteNameHierarchy}", headers=headers2)

	res = conn.getresponse()
	data = res.read()
	sitehi = data.decode("utf-8")
	sitehi = json.loads(sitehi)
	sitehi2 = sitehi['response']

	##>>> sitehi2[0]['siteNameHierarchy']
	##'Global/Research Triangle Park/RTP7-4/4th Floor'
	##>>> sitehi2[0]['id']
	##'78eacd6e-1d34-4027-9fda-b76cbb495aaf'

	return sitehi2[0]['id'], sitehi2[0]['siteNameHierarchy']

def get_devicelist(serialNumber, headers2, conn):
	""" Get Device list API - Returns device waiting to be claimed that matches SN """

	conn.request("GET", f"/dna/intent/api/v1/onboarding/pnp-device?serialNumber={serialNumber}", headers=headers2)

	res = conn.getresponse()
	data = res.read()
	data = data.decode("utf-8")
	devices = json.loads(data)

	##>>> devices[0]['deviceInfo']['serialNumber']
	##'DEMO0000002'
	##>>> devices[0]['id']
	##'5dc7a74fbbd19e0008392a89'

	return devices[0]['id'], devices[0]['deviceInfo']['serialNumber'], devices[0]['deviceInfo']['hostname'], devices[0]['deviceInfo']['pid']

def get_template(templatePick, headers2, conn):
	"""Gets the templates available API"""

	conn.request("GET", "/dna/intent/api/v1/template-programmer/template", headers=headers2)

	res = conn.getresponse()
	data = res.read()
	data = data.decode("utf-8")
	templatelist = json.loads(data)
	##>>> templatelist[12]['name']
	##'Basic Config'

	for t in templatelist:

		if t['name'] == templatePick:
			
			return t['templateId'], t['name']

def claim_device(id_site2, id_device2, id_template2, headers2, conn, configvar ):
	"""
	Claim a Device to a Site API - Usings site id, device id, and template id that was previously obtained.

	API documentation is wrong on this section. See bug CSCvq87348 

	"""

	body2 = {	
       "siteId": id_site2,
       "deviceId": id_device2,
       "type": "Default",
       "imageInfo": {
              "imageId": "optionalOverrideImageId",
              "reload": False,
              "skip": True
       },
       "configInfo": {
              "configId": id_template2,
              "configParameters": configvar,
              "saveToStartUp": True,
              "connLossRollBack": True
       }
	}

	body2 = bytes(json.dumps(body2), encoding="utf-8")	## have to convert body to bytes to be compatible

	conn.request("POST", "/dna/intent/api/v1/onboarding/pnp-device/site-claim", body = body2, headers=headers2)
	res = conn.getresponse()
	data = res.read()
	data = data.decode("utf-8")
	claimstat = json.loads(data)

	return claimstat['response']


main()


