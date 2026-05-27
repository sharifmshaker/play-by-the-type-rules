import os
from lotus.dtype_extensions import ImageArray


def run(con):
    data_dir = "./files/ecomm/data/sf_500/"
    image_mapping = con.execute("SELECT * FROM image_mapping").df()
    styles_details = con.execute("SELECT * FROM styles_details").df()

    # Pre-filter data
    styles_details = styles_details[
        styles_details["baseColour"].isin(
            ["Black", "Blue", "Red", "White", "Orange", "Green"]
        )
        & (styles_details["colour1"] == "")
        & (styles_details["colour2"] == "")
        & (styles_details["price"] < 800)
    ]
    image_mapping = image_mapping[
        image_mapping["id"].astype("int").isin(styles_details["id"])
    ]
    image_mapping["images"] = ImageArray(
        image_mapping.filename.apply(
            lambda s: os.path.join(data_dir, "images", s)
        )
    )

    # Self-join
    join_instruction = """
     Determine whether both images display objects of the same category
     (e.g., both are shoes, both are bags, etc.) and whether these objects
     share the same dominant surface color. Disregard any logos, text, or
     printed graphics on the objects. There might be other objects in the
     images. Only focus on the main object. Base your comparison solely on
     object type and overall surface color: {images:left} {images:right}
    """

    processed = image_mapping.sem_join(image_mapping, join_instruction)

    # Remove identical join partners
    processed = processed[processed["id:left"] != processed["id:right"]]

    processed["id"] = (
        processed["id:left"].astype("str")
        + "-"
        + processed["id:right"].astype("str")
    )
    return processed["id"]