# coding=utf8
from xpinyin import Pinyin

p = Pinyin()
# p.get_pinyin('上海')
print p.get_pinyin('上海', '')
print p.get_initials(u"上海", u'').lower()