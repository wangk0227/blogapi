'''返回的数据结构'''


class BaseResponse:
    def __init__(self):
        self.code = None
        self.error = None
        self.data = None

    @property
    def dict(self):
        return self.__dict__
