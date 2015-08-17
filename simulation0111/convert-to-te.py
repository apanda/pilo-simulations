#!/usr/bin/env python
import yaml
import sys
inp = open(sys.argv[1]).read()
y = yaml.load(inp)
for (k, v) in y.iteritems():
    if isinstance(v, dict):
        if 'type' in v and v['type'] == 'LSGossipControl':
            v['type'] = 'LSTEControl'
print yaml.dump(y)
