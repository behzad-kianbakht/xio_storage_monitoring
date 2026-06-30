from pyzabbix import ZabbixMetric, ZabbixSender
import requests
import warnings
from requests.auth import HTTPBasicAuth
import json
import sys
import time

alert_ignore_list = ["clear","acknowledged"]

script_type = sys.argv[1]
XIO_IP = sys.argv[2]
Zabbix_Host_name = sys.argv[3]

Zabbix_Interface_IP = "127.0.0.1"
Zabbix_discovery_alert_key = "XIO_Create_Alert"

# Disable SSL warnings (InsecureRequestWarning)
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning) # type: ignore

# Set up the request parameters
url = f'https://{XIO_IP}/api/json/v2/types/alerts'
username = 'XIO_REST_API_USERNAME'
password = 'XIO_REST_PASSWORD'

try:
# Send the GET request to fetch the list of alerts
    response = requests.get(url, auth=HTTPBasicAuth(username, password), verify=False,timeout=20)
    packet = [ZabbixMetric(host=Zabbix_Host_name, key="ALERT_XIO_Status", value=1)]
    zbx = ZabbixSender(Zabbix_Interface_IP)
    zbx.timeout = 1000
    output = zbx.send(packet)
    print(output)
    #time.sleep(100)
except:
    packet = [ZabbixMetric(host=Zabbix_Host_name, key="ALERT_XIO_Status", value=0)]
    zbx = ZabbixSender(Zabbix_Interface_IP)
    zbx.timeout = 1000
    output = zbx.send(packet)
    print(output)
    #time.sleep(100)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    alert_discovery = []
    # Extract the 'href' values from the 'alerts' list
    hrefs = [alert['href'] for alert in data['alerts']]
    
    # Loop through each alert's 'href' and send a request to fetch detailed data
    for href in hrefs:
        # Fetch the detailed alert information
        alert_response = requests.get(href, auth=HTTPBasicAuth(username, password), verify=False)
        
        if alert_response.status_code == 200:
            # Parse the detailed alert response
            alert_data = alert_response.json()
            content = alert_data['content']
            
            # Extract required fields
            assoc_obj_name = content.get('assoc-obj-name', 'N/A')
            description = content.get('description', 'N/A')
            class_name = content.get('class-name', 'N/A')
            alert_type = content.get('alert-type', 'N/A')
            alert_state = content.get('alert-state', 'N/A')
            sys_name = content.get('sys-name', 'N/A')
            severity = content.get('severity', 'N/A')
            href_value = href  # Use the href from the previous loop
            
            if all(alert_ignore not in alert_state for alert_ignore in alert_ignore_list):
                # Print the extracted data
                print(f"assoc-obj-name: {assoc_obj_name}")
                print(f"description: {description}")
                print(f"class-name: {class_name}")
                print(f"alert-type: {alert_type}")
                print(f"alert-state: {alert_state}")
                print(f"sys-name: {sys_name}")
                print(f"severity: {severity}")
                print(f"href: {href_value}")
                print("-" * 50)  # Separator between alerts
                alert_discovery.append({
                    '{#ASSOBJNAME}' : assoc_obj_name,
                    '{#DISC}' : description,
                    '{#CLASSNAME}' : class_name,
                    '{#ALERTTYPE}' : alert_type,
                    '{#ALERTSTS}' : alert_state,
                    '{#SYSNAME}' : sys_name,
                    '{#SEV}' : severity,
                    '{#HREF}' : href_value
                })
            else:
                print(f"Alert Containe clear or acknowledged - {description}")
        else:
            print(f"Error fetching detailed alert data from {href}")
            
    alert_discovery_json = json.dumps(alert_discovery)
    #print(alert_discovery_json)
    packet = [ZabbixMetric(host=Zabbix_Host_name, key=Zabbix_discovery_alert_key, value=alert_discovery_json)]
    if script_type == "alert":
        try:
            zbx = ZabbixSender(Zabbix_Interface_IP)
            zbx.timeout = 1000
            output = zbx.send(packet)
            print(output)
            #time.sleep(100)

            for i in range(0,len(alert_discovery)):
                alert = alert_discovery[i]
                item_key = f"alert[{alert['{#SEV}']}-{alert['{#ASSOBJNAME}']}-{alert['{#DISC}']}]"
                packet = [ZabbixMetric(host=Zabbix_Host_name, key=item_key, value=1)]
                zbx = ZabbixSender(Zabbix_Interface_IP)
                zbx.timeout = 1000
                output = zbx.send(packet)
                print(f"Value : {output}")
                # alert[{#SEV}-{#ASSOBJNAME}-{#DISC}]
                print(packet)
        except Exception as e:
            print(f"Zabbix Connection Error: {e}")
            
else:
    # Print error message if the request to fetch alert list failed
    print(f"Error fetching alerts list: {response.status_code}")
