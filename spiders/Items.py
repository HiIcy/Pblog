# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/10
__File__      :  items.py
__Desc__      :
"""

# TODO:模仿 scrapy.item
from collections import OrderedDict

__all__ = ['UserItems', 'ArticleItems']


class Field:
    def __init__(self):
        self.value = ""

    # def __get__(self, instance, owner): # 只能做类属性
    # 	if self.value is not None:
    # 		return self.value
    # 	return ""
    # def __set__(self, instance, value):
    # 	print('sfsf')
    # 	self.value = value

    def __repr__(self):
        print('-----')
        if self.value is not None:
            return str(self.value)
        return ""


class Item(object):
    def __init__(self):
        self._value = OrderedDict()
        self._compose()
        self.apply()

    def apply(self):
        for field in self.__dict__.keys():
            value = self.__getattribute__(field)
            if not value or callable(value):
                continue
            self._value[field] = value

    def _compose(self):
        pass

    def unapply(self):
        return [self._value[key] for key in self._value.keys()]

    def __setitem__(self, key, value):
        assert key in self._value.keys()
        self._value[key] = value

    def __getitem__(self, item):
        assert item in self._value.keys()
        return self._value[item]

    def __delitem__(self, key):
        assert key in self._value.keys()
        del self._value[key]

    def __len__(self):
        return len(self._values)

# FIXME: FIELD 修改
class UserItems(Item):

    def __init__(self):
        super(UserItems, self).__init__()

    # TODO:重新修改Field:

    def _compose(self):
        self.name = Field()
        self.creates = Field()
        self.fans = Field()
        self.praises = Field()
        self.comments = Field()
        self.visits = Field()
        self.grade = Field()
        self.credits = Field()
        self.ranks = Field()
        self.badges = Field()
        self.url = Field()


class ArticleItems(Item):
    def _compose(self):
        self.title = Field()
        self.create_time = Field()
        self.read_count = Field()
        self.nature = Field()  # 考虑要不要存储转载or原创
        self.content = Field()
        self.praises = Field()
        self.comments = Field()
        self.url = Field()
        self.user_name = Field()


if __name__ == "__main__":
    j = UserItems()
    j['creates'] = 5
    j['fans'] = 10
    j['grade'] = 10
    j['comments'] = 100
    j['badges'] = "sfs"
    j['praises'] = 10
    j['name'] = 'ov'
    print(j.unapply())