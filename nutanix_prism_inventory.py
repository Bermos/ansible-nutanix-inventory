#!/usr/bin/env python3
import argparse
import os
import json
import requests
import urllib3
from requests.auth import HTTPBasicAuth


# Helper function to make API requests
def make_request(url, session, payload=None):
    headers = {"Content-Type": "application/json"}
    response = session.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


# Helper function to make API requests with pagination support
def make_paginated_request(url, session, payload=None):
    all_entities = []
    offset = 0
    limit = 50
    has_more = True

    while has_more:
        pl = {**payload, "offset": offset, "length": limit} if payload else {"offset": offset, "length": limit}
        result = make_request(url, session, pl)
        all_entities.extend(result["entities"])
        if "length" in result["metadata"]:
            has_more = offset + result["metadata"]["length"] < result["metadata"]["total_matches"]
        else:
            has_more = False
        offset += limit

    return all_entities


def get_guest_customization_type(vm_resources):
    if "guest_customization" in vm_resources:
        if "sysprep" in vm_resources["guest_customization"]:
            return "sysprep"
        elif "cloud_init" in vm_resources["guest_customization"]:
            return "cloud_init"
        else:
            return None
    else:
        return None


def parse_cli_args():
    parser = argparse.ArgumentParser(description='Produce an Ansible inventory file from Nutanix')

    parser.add_argument('--list', action='store_true', default=True, help='List all hosts, defaults to true')
    parser.add_argument('--host', default=None, help='Get all the variables about a specific host')
    parser.add_argument('--pretty', action='store_true', help='JSON pretty-print')

    return parser.parse_args()


def main():
    args = parse_cli_args()

    # Retrieve environment variables
    prism_central_host = os.environ.get("PRISM_CENTRAL_HOST")
    prism_central_username = os.environ.get("PRISM_CENTRAL_USERNAME")
    prism_central_password = os.environ.get("PRISM_CENTRAL_PASSWORD")
    verify_ssl = os.environ.get("VERIFY_SSL", "true").lower() == "true"

    # Check for required environment variables
    if not prism_central_host or not prism_central_username or not prism_central_password:
        raise ValueError("PRISM_CENTRAL_HOST, PRISM_CENTRAL_USERNAME, and PRISM_CENTRAL_PASSWORD must be set.")

    # Define the API base URL
    api_base_url = f"https://{prism_central_host}:9440/api/nutanix/v3"

    # Initialize the session with basic authentication
    session = requests.Session()
    session.auth = HTTPBasicAuth(prism_central_username, prism_central_password)
    session.verify = verify_ssl
    urllib3.disable_warnings()

    # Retrieve categories and VMs
    vms = make_paginated_request(f"{api_base_url}/vms/list", session, {"kind": "vm"})
    clusters = make_paginated_request(f"{api_base_url}/clusters/list", session, {"kind": "cluster"})
    projects = make_paginated_request(f"{api_base_url}/projects/list", session, {"kind": "project"})
    os_types = make_paginated_request(f"{api_base_url}/categories/OSType/list", session, {"kind": "category"})

    # Create the inventory
    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "hosts": [],
            "children": []
        }
    }

    for cluster in clusters:
        inventory[cluster["spec"]["name"]] = {"hosts": [], "children": []}

    for os_type in os_types:
        inventory[os_type["value"]] = {"hosts": [], "children": []}

    for project in projects:
        inventory[project["spec"]["name"]] = {"hosts": [], "children": []}
    inventory["_internal"] = {"hosts": [], "children": []}

    # Add the VMs to the inventory
    for vm in vms:
        # Add the VM to the all group
        inventory["all"]["hosts"].append(vm["spec"]["name"])

        # Add the VM to the cluster group
        cluster_name = vm["spec"]["cluster_reference"]["name"]
        inventory[cluster_name]["hosts"].append(vm["spec"]["name"])

        # Add the VM to the project groups
        project_name = vm["metadata"]["project_reference"]["name"]
        inventory[project_name]["hosts"].append(vm["spec"]["name"])

        # Add the VM to the OS type groups
        if "OSType" in vm["metadata"]["categories"]:
            os_type = vm["metadata"]["categories"]["OSType"]
            inventory[os_type]["hosts"].append(vm["spec"]["name"])

        # Add hostvars for the VM
        inventory["_meta"]["hostvars"][vm["spec"]["name"]] = {
            "ansible_host": vm["status"]["resources"]["nic_list"][0]["ip_endpoint_list"][0]["ip"],
            "categories": vm["metadata"]["categories"],
            "nutanix_cluster": cluster_name,
            "nutanix_project": vm["metadata"]["project_reference"]["name"],
            "nutanix_owner": vm["metadata"]["owner_reference"]["name"],
            "nutanix_description": vm["status"]["description"] if "description" in vm["status"] else None,
            "nutanix_power_state": vm["status"]["resources"]["power_state"],
            "nutanix_num_sockets": vm["status"]["resources"]["num_sockets"],
            "nutanix_num_vcpus_per_socket": vm["status"]["resources"]["num_vcpus_per_socket"],
            "nutanix_memory_size_mib": vm["status"]["resources"]["memory_size_mib"],
            "nutanix_machine_type": vm["status"]["resources"]["machine_type"],
            "nutanix_guest_customization_type": get_guest_customization_type(vm["status"]["resources"]),
            "nutanix_subnet_name": vm["status"]["resources"]["nic_list"][0]["subnet_reference"]["name"],
        }

    indent = 2 if args.pretty else None
    if args.host:
        # Output a specific host's variables
        print(json.dumps(inventory["_meta"]["hostvars"][args.host], indent=indent))
        return
    else:
        # Output the inventory as JSON
        print(json.dumps(inventory, indent=indent))


if __name__ == '__main__':
    main()
