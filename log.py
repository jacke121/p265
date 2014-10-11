import sys
import logging

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

main = logging.getLogger("p265")
main.addHandler(logging.FileHandler(filename="p265.log", mode='w'))

syntax = logging.getLogger("p265.syntax_element")
syntax.addHandler(logging.FileHandler(filename="syntax_element.log", mode='w'))

cabac = logging.getLogger("p265.cabac")
cabac.addHandler(logging.FileHandler(filename="cabac.log", mode='w'))
