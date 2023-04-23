#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from socket import AF_X25

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', type=str)
    parser.add_argument('-p', action='store_true')
    args = parser.parse_args()
    path = args.directory
    flag = args.p
    print('type: ', type(flag), ' f = ', flag)
    print('path: ', path)
