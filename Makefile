.PHONY: vendor
vendor:
	pip3 install -r requirements.txt --python-version 3.10.5 --platform manylinux2014_x86_64 --only-binary=:all: --target=./vendor

.PHONY: deploy
deploy:
	rm -rf vendor
	make vendor
	neru deploy