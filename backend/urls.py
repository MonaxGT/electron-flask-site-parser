from collections import namedtuple

from typing import List
from flask_restful import Api


APIResource = namedtuple('URLPattern', ('resource', 'endpoint'))


urlpatterns: List[APIResource] = [

]


def apply_resources(api: Api):
    for res in urlpatterns:
        api.add_resource(res.resource, endpoint=res.endpoint)
