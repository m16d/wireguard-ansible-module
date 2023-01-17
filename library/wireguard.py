#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import subprocess

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
        if check_mode:
            module.exit_json(changed=True)
        else:
            create_or_update_interface(module, name, listen_port, addresses, peers)

    elif state == 'absent':
        if check_interface_exists(module, name):
            if check_mode:
                module.exit_json(changed=True)
            else:
            # Delete the WireGuard interface
                delete_interface(module, name)
                module.exit_json(changed=True, msg="Successfully deleted WireGuard interface")
        else:
            module.exit_json(changed=False, msg="WireGuard interface does not exist")

def create_or_update_interface(module, name, listen_port, addresses, peers):
    # Generate the private key and public key
    private_key, public_key = generate_key()

    # Check if the interface already exists
    interface_exists = check_interface_exists(module, name)

    # If the interface does not exist, create it
    if not interface_exists:
        create_interface(module, name, private_key, public_key, listen_port, addresses, peers)
    else:
        # If the interface exists, update it
        update_interface(module, name, private_key, public_key, listen_port, addresses, peers)

def generate_key():
    private_key = subprocess.check_output(["wg", "genkey"])
    public_key = subprocess.check_output(["wg", "pubkey"], input=private_key)
    return private_key, public_key

def create_interface(module, name, private_key, public_key, listen_port, addresses, peers):
    # Use the wg command to create the interface
    # Example: wg setconf wg0 /etc/wireguard/wg0.conf
    command = "wg setconf {0} /etc/wireguard/{0}.conf".format(name)
    rc, out, err = module.run_command(command)

    # Check if the command was successful
    if rc != 0:
        module.fail_json(msg="Failed to create WireGuard interface: {0}".format(err))
    else:
        # Generate the config file
        generate_config_file(module, name, private_key, public_key, listen_port, addresses, peers)
        module.exit_json(changed=True, msg="Successfully created WireGuard interface", public_key=public_key)

def update_interface(module, name, private_key, public_key, listen_port, addresses, peers):
    # Use the wg command to update the interface
    # Example: wg setconf wg0 /etc/wireguard/wg0.conf
    command = "wg setconf {0} /etc/wireguard/{0}.conf".format(name)
    rc, out, err = module.run_command(command)

    # Check if the command was successful
    if rc != 0:
        module.fail_json(msg="Failed to update WireGuard interface: {0}".format(err))
    else:
        # Generate the config file
        generate_config_file(module, name, private_key, public_key, listen_port, addresses, peers)
        module.exit_json(changed=True, msg="Successfully updated WireGuard interface", public_key=public_key)

def generate_config_file(module, name, private_key, public_key, listen_port, addresses, peers):
    # Create the config file
    config_file = open("/etc/wireguard/{0}.conf".format(name), "w")
    config_file.write("[Interface]\n")
    config_file.write("PrivateKey = {0}\n".format(private_key))
    config_file.write("ListenPort = {0}\n".format(listen_port))
    config_file.write("Address = {0}\n".format(' '.join(addresses)))
    config_file.write("\n")

    for peer in peers:
        config_file.write("[Peer]\n")
        config_file.write("PublicKey = {0}\n".format(peer['public_key']))
        config_file.write("AllowedIPs = {0}\n".format(peer['allowed_ips']))
        config_file.write("Endpoint = {0}:{1}\n".format(peer['endpoint']['address'],peer['endpoint']['port']))
        if 'persistent_keepalive' in peer:
            config_file.write("PersistentKeepalive = {0}\n".format(peer['persistent_keepalive']))
        config_file.write("\n")
        
    config_file.close()
    
def delete_interface(module, name):
    # Use the wg command to delete the interface
    # Example: wg-quick down wg0
    command = "wg-quick down {0}".format(name)
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
