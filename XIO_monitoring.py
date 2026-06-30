
from pyzabbix import ZabbixMetric, ZabbixSender
import requests
import urllib3
import json
import time
from concurrent.futures import ThreadPoolExecutor
import sys
from typing import Dict, Optional, Any

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Zabbix Connection Details
Zabbix_Interface_IP = "127.0.0.1"
Zabbix_discovery_key_N = "XIO_Create_Item_N"
Zabbix_discovery_key_S = "XIO_Create_Item_S"
Zabbix_Host_name = sys.argv[3] #"T3-X2-1"

# Constants
XIO_IP = sys.argv[2] # " XIO Managmnet IP"
XIO_BASE_URL = f"https://{XIO_IP}/api/json/v3"
XIO_USERNAME = "XIO_USER_NAME"
XIO_PASSWORD = "XIO_REST_API_PASSWORD"

# REST Session for connection reuse
session = requests.Session()
session.auth = (XIO_USERNAME, XIO_PASSWORD)
session.verify = False

def list_objects(object_type_href: str) -> Dict[str, str]:
    """Fetch and list all objects of a given type."""
    try:
        response = session.get(object_type_href)
        response.raise_for_status()
        objects_key = object_type_href.split("/")[-1]
        objects = response.json().get(objects_key, [])
        return {obj.get("name", "unknown"): obj.get("href", "") for obj in objects}
    except requests.exceptions.RequestException as e:
        print(f"Error listing objects for {object_type_href}: {e}")
        return {}

def get_object_details(object_href: str) -> Optional[Dict[str, Any]]:
    """Fetch details for a specific object."""
    try:
        response = session.get(object_href)
        response.raise_for_status()
        return response.json().get("content", {})
    except requests.exceptions.RequestException as e:
        print(f"Error fetching object details: {e}")
        return {}

def detect_type(value: Any) -> Optional[Any]:
    """Detect the type of the value and convert if possible."""
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    else:
        return None

def fetch_all_data(input_type: str, input_metric: str, type_href: str):
    """Fetch data for the specified type and metric."""
    print(f"Fetching data for {input_type} and metric {input_metric}...")
    discovery_list = []
    
    # Fetch objects for the given type
    objects = list_objects(type_href)
    for obj_name, obj_href in objects.items():
        print(f"\nFetching details for {input_type} '{obj_name}'...")
        object_details = get_object_details(obj_href)
        if object_details:
            metric_value = object_details.get(input_metric)
            # Add to discovery list
            discovery_list_dic = [{
                '{#TYPENAME}': input_type,
                '{#OBJNAME}': obj_name,
                '{#OBJDETAILS}': input_metric
            }]
            discovery_list = json.dumps(discovery_list_dic)
            print(discovery_list)
            
            checked_value_type = detect_type(metric_value)    
            if script_type == "value":
                packet = []
                if isinstance(checked_value_type, (int, float)):
                    zabbix_value_key = f"XIO_N_[{input_type},{obj_name},{input_metric}]"
                elif isinstance(checked_value_type, str):
                    zabbix_value_key = f"XIO_S_[{input_type},{obj_name},{input_metric}]"
                packet = [ZabbixMetric(host=Zabbix_Host_name, key=zabbix_value_key, value=checked_value_type)]
                print(packet)
                try:
                    zbx = ZabbixSender(Zabbix_Interface_IP)
                    zbx.timeout = 1000
                    output = zbx.send(packet)
                    print(output)
                except Exception as e:
                    print(f"Zabbix Connection Error: {e}")

            elif script_type == "discovery":
                packet = []
                if isinstance(checked_value_type, (int, float)):
                    zabbix_discovery_key = Zabbix_discovery_key_N
                elif isinstance(checked_value_type, str):
                    zabbix_discovery_key = Zabbix_discovery_key_S
                packet = [ZabbixMetric(host=Zabbix_Host_name, key=zabbix_discovery_key, value=discovery_list)]
                print(packet)
                try:
                    zbx = ZabbixSender(Zabbix_Interface_IP)
                    zbx.timeout = 1000
                    output = zbx.send(packet)
                    print(output)
                except Exception as e:
                    print(f"Zabbix Connection Error: {e}")

            else:
                print("Script Type Not defined Correctly : value or discovery")

# Main execution logic with ThreadPoolExecutor
if __name__ == "__main__":
    script_type = sys.argv[1]
    data = {
                "clusters": [
                                "thin-provisioning-ratio", 
                                "data-reduction-ratio-text", 
                                "vol-size", 
                                "logical-space-in-use", 
                                "ud-ssd-space", 
                                "ud-ssd-space-in-use",
                                "num-of-ssds",
                                "sys-sw-version",
                                "max-volume",
                                "sys-state",
                                "sys-health-state",             # Monitors overall system health. Current value
                                "obj-severity",                 # Indicates severity level of active issues. Current value
                                "ssd-high-utilization-thld-crossing",  # Tracks SSD utilization thresholds. Current value
                                "dae-temperature-monitor-mode", # Ensures proper monitoring of disk array enclosure temperatures. Current value
                                "free-ud-ssd-space-in-percent", # Tracks the percentage of free SSD space
                                "shared-memory-in-use-ratio",   # Reflects shared memory usage for cluster operations.
                                "avg-latency",                  # Average system latency. (microseconds).
                                "bw",                           # Bandwidth utilization for reads and writes
                                "num-of-critical-alerts"        # Tracks the number of critical alerts. Current value: 0.
                            ],
                "lun-maps" : [
                                "ig-name",           # Name of the Initiator Group (IG) that identifies the host or host group accessing the LUN.
                                "vol-name",          # Name of the volume being mapped to the host or host group.
                                #"tg-name",           # Name of the Target Group (TG) specifying the targets available for the LUN.
                                #"obj-severity",      # Severity level of the mapping object, indicating its health or status (e.g., "information", "warning", "critical").
                                #"certainty",         # Status indicating the validity or certainty of the LUN mapping configuration (e.g., "ok", "error").
                                #"mapping-id",        # Unique identifier for the LUN mapping, used for tracking and troubleshooting.
                                #"lun"                # Logical Unit Number (LUN) assigned to the volume for the specified initiator.
                            ],
                "dae-controllers" : [
                                "fru-lifecycle-state",          # Indicates the health of the FRU (Field Replaceable Unit), e.g., "healthy" or "faulty".
                                "port-state",                   # The operational state of the port, essential for understanding the connectivity status (e.g., "up" or "down").
                                "temperature-state",            # Tracks the temperature state (e.g., "normal"), critical for preventing overheating and ensuring proper cooling.
                                #"sas1-port-health-state",       # The health state of the SAS1 port (e.g., "healthy" or "faulty").
                                #"sas2-port-health-state",       # The health state of the SAS2 port (e.g., "healthy" or "faulty").
                                #"sas1-port-rate",               # The transfer rate of the SAS1 port, indicating potential bottlenecks (e.g., "12gbps").
                                #"sas2-port-rate",               # The transfer rate of the SAS2 port, another performance indicator (e.g., "12gbps").
                                #"sas1-last-24h-number-of-phy-problems",  # The number of physical issues detected on SAS1 port in the last 24 hours (important for monitoring failures).
                                #"sas2-last-24h-number-of-phy-problems",  # The number of physical issues detected on SAS2 port in the last 24 hours.
                                #"last-24h-number-of-phy-problems",       # General physical problems over the last 24 hours, relevant for early failure detection.
                                #"port-health-level",            # A health level indicator for the port, providing a summary of the port's overall status (e.g., "level_1_clear").
                                #"fw-version-error",             # Indicates any firmware errors, important for troubleshooting firmware-related issues.
                                "status-led",                   # Status LED of the controller (e.g., "off" or "on"), which can indicate hardware issues.
                                "enabled-state",                # Whether the controller is enabled or not, crucial for operational status.
                                "model-name",                   # The model name of the controller, useful for identifying its capabilities and hardware specs.
                                "serial-number",                # Serial number for identification, support, and warranty purposes.
                                "lcc-health-level",             # Health level of the LCC (Logical Control Card), provides insight into the health of the controller card.
                            ],
                "storage-controllers": [
                                "name",                             # Name of the controller, essential for identification (e.g., "X1-SC1").
                                "fru-lifecycle-state",              # Indicates the health of the FRU (Field Replaceable Unit), e.g., "healthy" or "faulty".
                                "serial-number",                    # Serial number for identification, support, and warranty purposes (e.g., "FC6XI184100071").
                                "part-number",                      # Part number of the controller, useful for identifying hardware components.
                                "model-name",                       # The model name of the controller, useful for identifying its capabilities and specs (e.g., "S2600WTT").
                                "bios-fw-version",                  # Firmware version of the BIOS, critical for compatibility and stability (e.g., "SE5C610.86B.01.01.3021.C1.051020171131").
                                #"fc-hba-model",                     # Fibre Channel HBA model, crucial for SAN connectivity and performance (e.g., "Emulex").
                                #"fc-hba-fw-version",                # Firmware version of the FC HBA, significant for SAN performance (e.g., "11.1.238.31").
                                #"pci-disk-controller-fw-version",   # Firmware version of the PCI disk controller (e.g., "12.35.04.00"), essential for stability and performance.
                                #"sas1-port-rate",                   # Transfer rate of the SAS1 port (e.g., "12gbps"), important for performance benchmarking.
                                #"sas2-port-rate",                   # Transfer rate of the SAS2 port (e.g., "12gbps"), another performance indicator.
                                "sas1-port-health-state",           # The health state of the SAS1 port (e.g., "healthy" or "faulty").
                                "sas2-port-health-state",           # The health state of the SAS2 port (e.g., "healthy" or "faulty").
                                #"sas1-last-24h-number-of-phy-problems",  # Physical problems detected on SAS1 port in the last 24 hours, critical for identifying performance bottlenecks.
                                #"sas2-last-24h-number-of-phy-problems",  # Physical problems detected on SAS2 port in the last 24 hours.
                                "temperature-health-state",         # Tracks the temperature state (e.g., "normal"), critical for preventing overheating and ensuring proper cooling.
                                "status-led",                       # Status LED of the controller (e.g., "off" or "on"), which can indicate hardware issues.
                                #"enabled-state",                    # Whether the controller is enabled or not, crucial for operational status.
                                "sas1-port-state",                  # Operational state of the SAS1 port (e.g., "up" or "down").
                                "sas2-port-state",                  # Operational state of the SAS2 port (e.g., "up" or "down").
                                "node-health-state",                # Overall health state of the node (e.g., "healthy").
                                #"ib1-link-rate-in-gbps",            # Infiniband IB1 link speed (e.g., "fdr"), important for high-speed network performance.
                                #"ib2-link-rate-in-gbps",            # Infiniband IB2 link speed (e.g., "fdr"), for evaluating network throughput.
                                "ib1-port-health-state",            # Health state of the IB1 port (e.g., "healthy" or "faulty").
                                "ib2-port-health-state",            # Health state of the IB2 port (e.g., "healthy" or "faulty").
                                #"mgmt-port-speed",                  # Management port speed (e.g., "1gb"), relevant for administrative connectivity.
                                "mgmt-port-state",                  # Operational state of the management port (e.g., "up").
                                "bmc-status-green-led",             # Green LED status of the BMC (Baseboard Management Controller), an indicator of normal operation.
                                "bmc-status-amber-led",             # Amber LED status of the BMC, indicating warnings or errors (e.g., "blinking").
                                "temperature-state",                # Temperature state of the node or controller, ensuring optimal conditions.
                                "voltage-health-state",             # Indicates voltage levels' health (e.g., "level_1_clear"), critical for power management.
                                "journal-state",                    # Health of the controller’s journaling system, ensuring data consistency.
                                "kdump-daemon-state",               # State of the kernel crash dump service, important for debugging and stability.
                                "fw-version-error",                 # Indicates any firmware errors, important for troubleshooting firmware-related issues.
                                "current-health-state",             # Overall current health state (e.g., "level_1_clear").
                                "num-of-local-disks",               # Number of local disks attached to the controller (e.g., "3"), impacting storage capacity and I/O.
                                "num-of-ssds",                      # Number of SSDs managed by the controller (e.g., "72"), crucial for storage performance.
                                #"acc-dimm-correctable-errors",      # Count of correctable DIMM errors, relevant for memory reliability.
                                #"dimm-correctable-errors",          # Total number of correctable memory errors, useful for early hardware issue detection.
                                #"backend-storage-controller-state", # State of the backend storage controller (e.g., "normal"), critical for storage reliability.
                                "upgrade-state",                    # State of any ongoing or completed upgrades (e.g., "no_upgrade_done").
                                "identify-led",                     # Status of the identify LED (e.g., "off"), helpful for physical hardware identification.
                                "os-version",                       # Operating System version (e.g., "Xtremio OS release 6.3.2-8_X2"), critical for software compatibility.
                                "sw-version",                       # Software version running on the controller (e.g., "6.3.2"), important for feature support.
                                "brick-name",                       # Name of the associated brick (e.g., "X1"), identifying the cluster component.
                                "sc-start-timestamp-display",       # Controller start time (e.g., "Sun Jan 24 04:40:57 2021"), useful for uptime calculations.
                                "node-mgr-addr",                    # IP address of the node manager (e.g., "10.218.108.11"), relevant for management connectivity.
                                "mgmt-link-health-level",           # Health level of the management link (e.g., "level_1_clear"), for ensuring stable connectivity.
                ],
                "volumes": [
                                "name",                            # Name of the volume, crucial for identification (e.g., "X2_1_t3dclm-bomdb02_1").
                                "vol-id",                          # Unique ID of the volume, essential for tracking and management.
                                "vol-size",                        # Volume size in bytes, important for capacity planning (e.g., "1073741824").
                                "iops",                            # Total Input/Output operations per second, indicating performance (e.g., "447").
                                "bw",                              # Bandwidth in KBps, a key performance metric (e.g., "11198").
                                "rd-iops",                         # Read IOPS, measuring read performance (e.g., "447").
                                "wr-iops",                         # Write IOPS, measuring write performance (e.g., "0").
                                "rd-bw",                           # Read bandwidth in KBps, for read performance monitoring (e.g., "11198").
                                "wr-bw",                           # Write bandwidth in KBps, for write performance monitoring (e.g., "0").
                                "unaligned-iops",                  # Unaligned IOPS, indicating inefficient IO operations (e.g., "302").
                                "unaligned-bw",                    # Unaligned bandwidth in KBps, highlighting misaligned workloads (e.g., "9001").
                                "avg-latency",                     # Average latency in microseconds, critical for assessing performance (e.g., "422").
                                "rd-latency",                      # Read latency in microseconds, showing read delay (e.g., "422").
                                "small-iops",                      # Small IO operations per second, indicating smaller transactions (e.g., "248").
                                #"logical-space-in-use",            # Logical space used by the volume, critical for utilization tracking (e.g., "514693712").
                                #"num-of-lun-mappings",             # Number of LUN mappings, relevant for volume access (e.g., "1").
                                #"secured-snap",                    # Indicates whether secured snapshots are enabled, important for data protection (e.g., "false").
                                #"unaligned-io-ratio",              # Percentage of unaligned IO, an efficiency indicator (e.g., "66").
                                #"data-reduction-ratio",            # Data reduction ratio, important for storage efficiency (e.g., "0").
                                #"creation-time",                   # Timestamp of volume creation, useful for lifecycle management (e.g., "2023-04-16 07:53:01").
                                #"vol-access",                      # Volume access level (e.g., "write_access"), crucial for permissions.
                                #"obj-severity",                    # Severity level of the object (e.g., "information"), useful for health alerts.
                                #"snapgrp-id",                      # Associated snapshot group IDs, important for snapshot management.
                                #"management-locked",               # Indicates if management access is locked, ensuring security (e.g., "false").
                                #"cert-certainty",                  # Status of the volume's operational certainty (e.g., "ok").
                                #"sys-name",                        # System name where the volume resides, linking to infrastructure (e.g., "T3-X2-1").
                ],
                "target-groups": [
                                "iops",                            # Total IOPS, indicating the input/output operations per second (e.g., "9378").
                                "bw",                              # Total bandwidth in KBps, critical for overall data throughput (e.g., "267643").
                                "rd-iops",                         # Read IOPS, indicating the performance of read operations (e.g., "2722").
                                "wr-iops",                         # Write IOPS, indicating the performance of write operations (e.g., "6656").
                                "rd-bw",                           # Read bandwidth in KBps, vital for read performance (e.g., "123627").
                                "wr-bw",                           # Write bandwidth in KBps, vital for write performance (e.g., "144016").
                                "unaligned-bw",                    # Bandwidth of unaligned IO operations (e.g., "151887").
                                "unaligned-wr-iops",               # Unaligned write IOPS, indicating inefficiencies (e.g., "2793").
                ],
                "ssds": [
                                "ssd-size",                        # The size of the SSD in bytes (e.g., "1875902464").
                                "model-name",
                                "brick-index",
                                "rg-name",
                                "slot-num",
                                "health-state",
                                #"fru-lifecycle-state",             # Indicates the health of the FRU (e.g., "healthy").
                                #"smart-error-ascq",                # SMART error ASCQ (If non-zero, indicates critical errors).
                                "iops",                            # Input/output operations per second (e.g., "132").
                                "rd-bw",                           # Read bandwidth in KBps (e.g., "1536").
                                "wr-iops",                         # Write IOPS, indicating write operations per second (e.g., "51").
                                #"fw-version-error",                # Firmware version error (e.g., "no_error").
                                "num-bad-sectors",                 # Number of bad sectors detected (e.g., "0").
                                "percent-endurance-remaining",     # Percentage of SSD endurance remaining (e.g., "79").
                                #"ssd-failure-reason",              # Reason for SSD failure, if any (e.g., "none").
                                "health-state",                    # Health status of the SSD, typically "normal".
                                #"ssd-link1-health-state",          # Health of SSD link 1 (e.g., "level_1_clear").
                                #"ssd-link2-health-state",          # Health of SSD link 2 (e.g., "level_1_clear").
                                "temperature-state",               # Temperature state of the SSD (e.g., "normal").
                                "rd-iops",                         # Read operations per second (e.g., "81").
                                "wr-bw",                           # Write bandwidth in KBps (e.g., "1029").
                                "ssd-space-in-use",                # SSD space used in bytes (e.g., "221838011").
                                "enabled-state",                   # Whether the SSD is enabled (e.g., "enabled").
                                #"status-led",                      # Status LED state (e.g., "off").
                                #"slot-state",                      # SSD slot state (e.g., "resident_ssd").
                                "diagnostic-health-state",         # Diagnostic health state (e.g., "level_1_clear").
                                "certainty",                       # Certainty of health status (e.g., "ok").
                                "smart-error-asc",                 # General SMART error ASC (e.g., "0").
                                "fw-version",                      # Firmware version (e.g., "PB4F").
                                #"slot-error-reason",               # Slot error reason (if any, e.g., "none").
                ],
                "infiniband-switches":[
                                "is-available",
                                "model-name",
                                "name",
                                "part-number",
                                "serial-number",
                                #"fan-module1-status",
                                #"fan-module2-status",
                                #"fan-module3-status",
                                #"fan-module4-status",
                ],
                "bricks":[
                                "configured-num-of-ssds",
                                "brick-state",
                                "num-of-ssds",
                                "num-of-nodes",
                                "name",
                ],
            }

    # Define the Hrefs for each type (hardcoded or passed dynamically)
    types_hrefs = {
        "clusters": f"{XIO_BASE_URL}/types/clusters",
        "lun-maps": f"{XIO_BASE_URL}/types/lun-maps",
        "dae-controllers" : f"{XIO_BASE_URL}/types/dae-controllers",
        "storage-controllers" : f"{XIO_BASE_URL}/types/storage-controllers",
        "volumes" : f"{XIO_BASE_URL}/types/volumes",
        "target-groups" : f"{XIO_BASE_URL}/types/target-groups",
        "ssds" : f"{XIO_BASE_URL}/types/ssds",
        "infiniband-switches" : f"{XIO_BASE_URL}/types/infiniband-switches",
        "bricks" : f"{XIO_BASE_URL}/types/bricks"
    }

    with ThreadPoolExecutor(max_workers=200) as executor:
        for parent_key, child_keys in data.items():
            # Get the type href for the current type
            type_href = types_hrefs.get(parent_key)
            if not type_href:
                print(f"Error: No href found for {parent_key}")
                continue

            for child_key in child_keys:
                input_type = parent_key
                input_metric = child_key
                print(f"Processing: {parent_key} {child_key}")
                executor.submit(fetch_all_data, input_type, input_metric, type_href)

    print("DONE")