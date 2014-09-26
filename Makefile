# This source is provided under the MIT License (see LICENSE.txt)
# Copyright (c) 2014 Ryan C. Catherman

TESTS := \
	./plugins/py/test/test_check_critical.py \
	./plugins/py/test/test_mac_to_ip.py \
	./plugins/py/test/test_nagiosplugins.py \
	./plugins/py/test/sample.py \

test-plugins:
	for test_ in $(TESTS); do\
    	PYTHONPATH=$(PYTHONPATH):$(CURDIR)/plugins/py/src/ $$test_ ; \
    done

test: test-plugins