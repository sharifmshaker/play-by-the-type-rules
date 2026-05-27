def run(con):
    styles_details = con.execute("SELECT * FROM styles_details").df()

    filtered = styles_details.sem_filter('The product is a backpack from Reebok: {productDisplayName} {productDescriptors}')

    return filtered[['id']]
