#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import wireguard

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
        create_or_update_interface(module, name, addresses, peers, check_mode)
    elif state == 'absent':
        delete_interface(module, name, check_mode)

def create_or_update_interface(module, name, addresses, peers, check_mode):
    wg = wireguard.WireGuard()

    try:
        interface = wg.interface(name)
        for address in addresses:
            interface.add_address(address)
        for peer in peers:
            interface.add_peer(peer)
        interface.save()
        if check_mode:
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=True, msg="Successfully created/updated WireGuard interface")
    except wireguard.WireGuardError as e:
        module.fail_json(msg=str(e))

def delete_interface(module, name, check_mode):
    wg = wireguard.WireGuard()

    try:
        interface = wg.interface(name)
        interface.remove()
        if check_mode:
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=True, msg="Successfully deleted WireGuard interface")
    except wireguard.WireGuardError as e:
        if e.errno == wireguard.errors.ENODEV:
            module.exit_json(changed=False, msg="WireGuard interface does not exist")
        else:
            module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
