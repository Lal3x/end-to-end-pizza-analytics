"""Descritores da fonte fixada; contrato em specs/ingestao.md."""

BASE_URL = "https://static.observableusercontent.com/files/"
FONTES = {
    "orders": {
        "arquivo": "orders.parquet",
        "colunas": ["id", "customerId", "storeId", "orderDate", "nItems", "total"],
        "tipos": ["INTEGER", "VARCHAR", "VARCHAR", "VARCHAR", "INTEGER", "DOUBLE"],
        "anexo": (
            "ede989ed5874365bf145962f00a2e8b4024c5d0de663cba68ee28dd66e75d335"
            "3a22a8c00769af5c08c0710c3d0a84834b2006643d65051cb388a20141f56b00"
        ),
        "sha256": "f88d964889bb11dde06b930513ff97bfc407353aedc101f1e4a97bd5acf5947a",
    },
    "order_items": {
        "arquivo": "order_items.parquet",
        "colunas": ["SKU", "orderID"],
        "tipos": ["VARCHAR", "INTEGER"],
        "anexo": (
            "30db2a0090eb4aa564f6d67a152a8a4bedb81bbb42a9c3ab06548b2bc9d5cc73"
            "9472df1b3785570efd376ecc0c8c6629e39a82aeee163d4bc68811360a97d152"
        ),
        "sha256": "cfef82b2403eb04542fa5af10b067dfdb0b45f54bdaa23152c782533fa2b7842",
    },
    "customers": {
        "arquivo": "customers.csv",
        "colunas": ["id", "latitude", "longitude"],
        "anexo": (
            "b6f9dc8144fe510cff0c8368dcf318f169c679581eae2e8ea6d1e5668e1d3343"
            "5d1e46d4e01e867a7438b08f9c57af45e2c3e4ea52d594aec6317c9770c3fb86"
        ),
        "sha256": "a4975208e7d3843fafbd53e5f1ed908530292d7f737ce91453466efa214f0231",
    },
    "stores": {
        "arquivo": "stores.csv",
        "colunas": [
            "id",
            "zipcode",
            "state_abbr",
            "latitude",
            "longitude",
            "city",
            "state",
            "distance",
        ],
        "anexo": (
            "b1837225ab1d3ee4b35b456b576fc971eaa3a0e2ec41da567af29c9cbacbc765"
            "fe7e85db3c0413c1174c1c420ed86d996c4df0c7b49b4bafb899195ba3b5a3b3"
        ),
        "sha256": "48a10f38803de9e904b4cf9a9b9eddc4af29c452e7968f211413bc342655c432",
    },
    "products": {
        "arquivo": "products.csv",
        "colunas": [
            "SKU",
            "Name",
            "Price",
            "Category",
            "Size",
            "Ingredients",
            "Launch",
        ],
        "anexo": (
            "9900712c2f529bb1bab6f2abd1d7b57aa73fdeea1e382628e91bf6a0366532d2"
            "1401aba2b3196a0c611c5a2109b463bf990410000e6aebf51f4fa85f968b10d1"
        ),
        "sha256": "c116092883ee22411c33a9c4a1b0dc68e8df26a26280a50ce10b9097366149e3",
    },
}
