#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess
import os
import shutil

def main():
    module = AnsibleModule(
        argument_spec={
            'listen_port': {'default': 51820, 'type': 'int'},
            'addresses': {'required': True, 'type': 'list'},
            'peers': {'required': True, 'type': 'list'},
            'name': {'default': 'wg0', 'type': 'str'},
            'state': {'default': 'present', 'choices': ['present', 'absent']}
        },
        supports_check_mode=True
    )

    listen_port = module.params['listen_port']
    addresses = module.params['addresses']
    peers = module.params['peers']
    name = module.params['name']
    state = module.params['state']
    check_mode = module.check_mode

    if state == 'present':
        create_or_update_interface_and_config(module, name, listen_port, addresses, peers, check_mode)
    elif state == 'absent':
        delete_interface_and_config(module, name, check_mode)

def create_or_update_interface_and_config(module, name, listen_port, addresses, peers, check_mode):
    if check_interface_exists(module, name) and check_config_file(module, name, listen_port, addresses, peers):
        module.exit_json(changed=False, msg="WireGuard interface is already in the desired state")
    elif check_mode:
        module.exit_json(changed=True)
    else:
        backup_config_file(module, name)
        private_key, public_key = generate_key()
        create_or_update_interface(module, name)
        generate_config_file(module, name, private_key, public_key, listen_port, addresses, peers)
        module.exit_json(changed=True, msg="Successfully created/updated WireGuard interface", public_key=public_key)

def delete_interface_and_config(module, name, check_mode):
    if check_interface_exists(module, name):
        if check_mode:
            module.exit_json(changed=True)
        else:
            delete_interface(module, name)
            remove_config_file(module, name)
            module.exit_json(changed=True, msg="Successfully deleted WireGuard interface")
    else:
        module.exit_json(changed=False, msg="WireGuard interface does not exist")

def remove_config_file(module, name):
    config_file_path = "/etc/wireguard/{0}.conf".format(name)
    os.remove(config_file_path)

def create_or_update_interface(module, name, listen_port, addresses, peers):
    # Generate the private key and public key
    private_key, public_key = generate_key()

    # Create/update the interface using wg
    command = "wg addconf {0}".format(name)
    rc, out, err = module.run_command(command)

    # Check if the command was successful
    if rc != 0:
        module.fail_json(msg="Failed to create/update WireGuard interface: {0}".format(err))
    else:
        # Generate the config file
        generate_config_file(module, name, private_key, public_key, listen_port, addresses, peers)
        module.exit_json(changed=True, msg="Successfully created/updated WireGuard interface", public_key=public_key)

def generate_key():
    private_key = subprocess.check_output(["wg", "genkey"])
    public_key = subprocess.check_output(["wg", "pubkey"], input=private_key)
    return private_key, public_key

def backup_config_file(module, name):
    config_file_path = "/etc/wireguard/{0}.conf".format(name)
    if os.path.exists(config_file_path):
        shutil.copy(config_file_path, config_file_path + ".backup")

def check_config_file(module, name, listen_port, addresses, peers):
    config_file_path = "/etc/wireguard/{0}.conf".format(name)
    if os.path.exists(config_file_path):
        # Compare the current config file with the desired config
        # Open the current config file
        config_file = open(config_file_path, 'r')
        current_config = config_file.read()
        config_file.close()
        # Generate the desired config
        desired_config = generate_config(listen_port, addresses, peers)
        # Compare the configs
        if current_config == desired_config:
            return True
        else:
            return False
    else:
        return False

def generate_config(listen_port, addresses, peers):
    config = "[Interface]\n"
    config += "ListenPort = {0}\n".format(listen_port)
    for address in addresses:
        config += "Address = {0}\n".format(address)
    config += "[Peer]\n"
    for peer in peers:
        config += "PublicKey = {0}\n".format(peer['public_key'])
        config += "AllowedIPs = {0}\n".format(peer['allowed_ips'])
        if 'endpoint' in peer:
            config += "Endpoint = {0}\n".format(peer['endpoint'])
    return config

    
def generate_config_file(module, name, private_key, public_key, listen_port, addresses, peers):
    config_file_path = "/etc/wireguard/{0}.conf".format(name)
    config_file = open(config_file_path, 'w')
    config_file.write("[Interface]\n")
    config_file.write("PrivateKey = {0}\n".format(private_key))
    config_file.write("ListenPort = {0}\n".format(listen_port))
    for address in addresses:
        config_file.write("Address = {0}\n".format(address))
    config_file.write("[Peer]\n")
    for peer in peers:
        config_file.write("PublicKey = {0}\n".format(peer['public_key']))
        config_file.write("AllowedIPs = {0}\n".format(peer['allowed_ips']))
        if 'endpoint' in peer:
            config_file.write("Endpoint = {0}\n".format(peer['endpoint']))
    config_file.close()

def delete_interface(module, name):
    # Use the wg command to delete the interface
    command = "wg delconf {0}".format(name)
    rc, out, err = module.run_command(command)

    # Check if the command was successful
    if rc != 0:
        module.fail_json(msg="Failed to delete WireGuard interface: {0}".format(err))
    else:
        module.exit_json(changed=True, msg="Successfully deleted WireGuard interface")

def check_interface_exists(module, name):
    # Use the wg command to check if the interface exists
    # Example: wg show wg0
    command = "wg show {0}".format(name)
    rc, out, err = module.run_command(command)

    # Check if the command was successful
    if rc != 0:
        return False
    else:
        return True

if __name__ == '__main__':
    main()
