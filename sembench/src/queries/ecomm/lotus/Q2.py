import os
from lotus.dtype_extensions import ImageArray

def run(con):
    data_dir = "./files/ecomm/data/sf_500/"
    image_mapping = con.execute("SELECT * FROM image_mapping").df()

    image_mapping['images'] = ImageArray(image_mapping.filename.apply(lambda s: os.path.join(data_dir, 'images', s)))

    # Filter data
    filtered = image_mapping.sem_filter('The image shows a (pair of) sports shoe(s) that feature the colors yellow and silver. {images}')

    return filtered['id']