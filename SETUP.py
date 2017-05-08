# -*- coding: utf-8 -*-

import pip

def get_dependencies():
    f = open("dependencies.txt")
    dependencies = [line.strip() for line in f]
    f.close()
    return dependencies

def install(package):
    pip.main(['install', package])

if __name__ == '__main__':
    for dependency in get_dependencies():
        install(dependency)