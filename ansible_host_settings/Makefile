.PHONY: venv ping list-tags run baseline k8s master-python

venv:
	./scripts/bootstrap_env.sh

ping:
	./.venv/bin/ansible -i inventory/hosts.ini all -m ping

list-tags:
	./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml --list-tags

run:
	./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml

baseline:
	./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml -t baseline

k8s:
	./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml -t k8s

master-python:
	./.venv/bin/ansible-playbook -i inventory/hosts.ini playbooks/site.yml -t master,python311
