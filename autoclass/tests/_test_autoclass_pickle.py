#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.

from autoclass import autoclass


@autoclass
class Foo(object):
    def __init__(self, foo1, foo2=0):
        pass


@autoclass
class Bar(Foo):
    def __init__(self, bar, foo1, foo2=0):
        # this constructor is not actually needed in this case since all fields are already self-assigned here
        super(Bar, self).__init__(foo1, foo2)
        # pass
