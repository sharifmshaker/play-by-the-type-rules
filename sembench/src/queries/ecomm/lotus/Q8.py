import os
from lotus.dtype_extensions import ImageArray

def run(con):
    data_dir = "./files/ecomm/data/sf_500/"
    # Load data
    image_mapping = con.execute("SELECT * FROM image_mapping").df()
    styles_details = con.execute("SELECT * FROM styles_details").df()

    # Pre-filter data
    styles_details = styles_details[styles_details.apply(
        lambda row: (
            row['productDescriptors'].get('description') is not None and
            row['productDescriptors']['description'].get('value') is not None and
            len(row['productDescriptors']['description']['value']) >= 3000
        ), axis=1
    )]
    # image_mapping = image_mapping[image_mapping['id'].astype('int').isin(styles_details['id'])]
    image_mapping['images']  = ImageArray(image_mapping.filename.apply(lambda s: os.path.join(data_dir, 'images', s)))

    # Perform joins
    processed = styles_details.sem_join(image_mapping, '''
     The image {images} fits the description: {productDisplayName} {productDescriptors}
    ''')

    processed['id'] = processed['id:left'].astype('str') + '-' + processed['id:right'].astype('str')
    return processed[['id']]