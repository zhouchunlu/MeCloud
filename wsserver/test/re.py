# coding=utf-8
from mecloud.lib import crypto

import re

if 'honey://emoji/' in 'honey://emoji/10':
    print 'in'
else:
    print 'not in'

a = 'honey://emoji/10'
print a.replace('honey://emoji/', '')

s='7c24696f6970243d21254d7077697572666f247969777c6978276a78797579362655782771776d787c756a7e727979296b826b74786b6e79703a2f382d30717f81507d7372314a2e403c2f327681825f8378344a32356d87494943786e884a4575466f8a4b4a4b4e718b4c464e4d728c51467d51738d524d4a53748e537b7f817590524c4c527791554b4c537892534f81517993555356507a945a54515a7b965a828688439f'
print crypto.decrypt(s)
