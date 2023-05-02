# Nutanix Prism Central Ansible Inventory

This script generates a dynamic Ansible inventory from Nutanix Prism Central. It groups VMs by Nutanix cluster, project, and OS type. Additionally, it provides host variables for each VM with useful information.

## Requirements

- Python 3.x
- `requests` package

To install the required Python package, run:

```bash
pip install requests
```

## Configuration

The script requires the following environment variables to be set:

- `PRISM_CENTRAL_HOST`: The Prism Central host (e.g., `prism.example.com`).
- `PRISM_CENTRAL_PORT` (optional): The Prism Central port (default: `9440`).
- `PRISM_CENTRAL_USERNAME`: The Prism Central username.
- `PRISM_CENTRAL_PASSWORD`: The Prism Central password.
- `VERIFY_SSL` (optional): Set to "false" to disable SSL certificate verification (default: "true").

You can set these environment variables in your shell session, or create a `.env` file in your project directory with the following content:

```
PRISM_CENTRAL_HOST=your_prism_central_host
PRISM_CENTRAL_USERNAME=your_prism_central_username
PRISM_CENTRAL_PASSWORD=your_prism_central_password
```

## Usage

To use the script as a dynamic inventory source, create a file named `ansible.cfg` in your project directory, or modify the existing one, and add the following configuration:

```ini
[defaults]
inventory = ./nutanix_prism_inventory.py
```

This will tell Ansible to use the `nutanix_prism_inventory.py` script as the inventory source. When you run an Ansible playbook or ad-hoc command, it will automatically use the generated inventory from the script.

To manually generate the inventory, run:

```bash
./nutanix_prism_inventory.py
```

You can add the `--pretty` flag to produce a more human-readable JSON output:

```bash
./nutanix_prism_inventory.py --pretty
```

## Inventory Groups

The script generates the following groups in the Ansible inventory:

- Clusters: A group for each Nutanix cluster with VMs.
- Projects: A group for each Nutanix project with VMs.
- OS Types: A group for each OS type with VMs.

Additionally, the `all` group is created, containing all VMs.

## Host Variables

The script provides host variables for each VM with the following information:

- `ansible_host`: The IP address of the VM.
- `categories`: The Nutanix categories for the VM.
- `nutanix_cluster`: The Nutanix cluster name.
- `nutanix_project`: The Nutanix project name.
- `nutanix_owner`: The Nutanix owner name.
- `nutanix_description`: The Nutanix description.
- `nutanix_power_state`: The Nutanix power state.
- `nutanix_num_sockets`: The Nutanix number of sockets.
- `nutanix_num_vcpus_per_socket`: The Nutanix number of vCPUs per socket.
- `nutanix_memory_size_mib`: The Nutanix memory size in MiB.
- `nutanix_machine_type`: The Nutanix machine type.
- `nutanix_guest_customization_type`: The Nutanix guest customization type (sysprep or cloud_init).
- `nutanix_subnet_name`: The Nutanix subnet name.

These host variables can be used in your Ansible playbooks and templates.