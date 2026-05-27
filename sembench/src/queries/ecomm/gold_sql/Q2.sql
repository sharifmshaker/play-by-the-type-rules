select id
from styles_details
where articleType.typeName = 'Sports Shoes'
and list_has_all([baseColour, colour1, colour2], ['Yellow', 'Silver']);