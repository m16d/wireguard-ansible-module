#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec={
            'private_key': {'required': True, 'type': 'str'},
            'listen_port': {'default': 51820, 'type': 'int'},
            'addresses': {'required': True, 'type': 'list'},
            'peers': {'required': True, 'type': 'list'},
            'name': {'default': 'wg0', 'type': 'str'},
            'state': {'default': 'present', 'choices': ['present', 'absent']}
        },
        supports_check_mode=True
    )

    private_key = module.params['private_key']
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
            # Create or update the WireGuard interface
            create_or_update_interface(module, name, private_key, listen_port, addresses, peers)
    elif state == 'absent':
        if check_mode:
            module.exit_json(changed=True)
        else:
            # Delete the WireGuard interface
            delete_interface(module, name)

def create_or_update_interface(module, name, private_key, listen_port, addresses, peers):
    # Check if the interface already exists
    interface_exists = check_interface_exists(module, name)

    # If the interface does not exist, create it
    if not interface_exists:
        create_interface(module, name, private_key, listen_port, addresses, peers)
    else:
        # If the interface exists, update it
        update_interface(module, name, private_key, listen_port, addresses, peers)

def create_interface(module, name, private_key, listen_port, addresses, peers):
    # Use the wg command to create the interface
    # Example: wg setconf wg0 /etc/wireguard/wg0.conf
    command = "wg setconf {0} /etc/wireguard/{0}.conf".format(name)
    rc, out, err = module.run_command(command)

    # Check if the command was successful
    if rc != 0:
        module.fail_json(msg="Failed to create WireGuard interface: {0}".format(err))
    else:
        module.exit_json(changed=True, msg="Successfully created WireGuard interface")

def update_interface(module, name, private_key, listen_port, addresses, peers):
    # Use the wg command to update the interface
    # Example: wg setconf wg0 /etc/wireguard/wg0.conf
    command = "wg setconf {0} /etc/wireguard/{0}.conf".format(name)
    rc, out, err = module.run_command(command)

    # Check if the command was successful
    if rc != 0:
        module.fail_json(msg="Failed to update WireGuard interface: {0}".format(err))
    else:
        module.exit_json(changed=True, msg="Successfully updated WireGuard interface")

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
