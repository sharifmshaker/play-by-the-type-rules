def run(con):
    data_dir = "./files/ecomm/data/sf_500/"
    # Load data
    styles_details = con.execute("SELECT * FROM styles_details").df()

    # Pre-filter data
    styles_details = styles_details[styles_details['price'] <= 500]

    # Self-join
    join_instruction = '''
     You will be given two product descriptions. Do both product descriptions describe
     products of the same category from the same brand, e.g., both are t-shirts from Adidas?

     The first product description is:
     {productDisplayName:left} - {productDescriptors:left}

     The second product description is:
     {productDisplayName:right} - {productDescriptors:right}
    '''

    processed = styles_details.sem_join(styles_details, join_instruction)

    processed['id'] = processed['id:left'].astype('str') + '-' + processed['id:right'].astype('str')
    return processed[['id']]