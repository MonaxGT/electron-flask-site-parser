from collections import namedtuple

from typing import List
from flask_restful import Api

import resources


APIResource = namedtuple('APIResource', ('resource', 'endpoint'))


urlpatterns: List[APIResource] = [
    APIResource(resources.BHFMessages, '/messages/bhf'),
    APIResource(resources.LolzMessages, '/messages/lolz')
]


def apply_resources(api: Api):
    for res in urlpatterns:
        api.add_resource(res.resource, res.endpoint)
