from base64 import urlsafe_b64encode
from typing import List, Optional, Union
from uuid import uuid4

# from lnbits.db import open_ext_db
from lnbits.db import SQLITE
from lnbits.helpers import urlsafe_short_hash
from lnbits.settings import WALLET

from . import db
from .models import (
    CreateMarket,
    CreateMarketStalls,
    Market,
    OrderDetail,
    Orders,
    Products,
    Stalls,
    Zones,
    createOrder,
    createOrderDetails,
    createProduct,
    createStalls,
    createZones,
)

###Products


async def create_diagonalley_product(data: createProduct) -> Products:
    product_id = urlsafe_short_hash()
    await db.execute(
        f"""
        INSERT INTO diagonalley.products (id, stall, product, categories, description, image, price, quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            data.stall,
            data.product,
            data.categories,
            data.description,
            data.image,
            data.price,
            data.quantity,
        ),
    )
    product = await get_diagonalley_product(product_id)
    assert product, "Newly created product couldn't be retrieved"
    return product


async def update_diagonalley_product(product_id: str, **kwargs) -> Optional[Stalls]:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])

    await db.execute(
        f"UPDATE diagonalley.products SET {q} WHERE id = ?",
        (*kwargs.values(), product_id),
    )
    row = await db.fetchone(
        "SELECT * FROM diagonalley.products WHERE id = ?", (product_id,)
    )

    return Products(**row) if row else None


async def get_diagonalley_product(product_id: str) -> Optional[Products]:
    row = await db.fetchone(
        "SELECT * FROM diagonalley.products WHERE id = ?", (product_id,)
    )
    return Products(**row) if row else None


async def get_diagonalley_products(stall_ids: Union[str, List[str]]) -> List[Products]:
    if isinstance(stall_ids, str):
        stall_ids = [stall_ids]

    # with open_ext_db("diagonalley") as db:
    q = ",".join(["?"] * len(stall_ids))
    rows = await db.fetchall(
        f"""
        SELECT * FROM diagonalley.products WHERE stall IN ({q})
        """,
        (*stall_ids,),
    )
    return [Products(**row) for row in rows]


async def delete_diagonalley_product(product_id: str) -> None:
    await db.execute("DELETE FROM diagonalley.products WHERE id = ?", (product_id,))


###zones


async def create_diagonalley_zone(user, data: createZones) -> Zones:
    zone_id = urlsafe_short_hash()
    await db.execute(
        f"""
        INSERT INTO diagonalley.zones (
            id,
            "user",
            cost,
            countries

        )
        VALUES (?, ?, ?, ?)
        """,
        (zone_id, user, data.cost, data.countries.lower()),
    )

    zone = await get_diagonalley_zone(zone_id)
    assert zone, "Newly created zone couldn't be retrieved"
    return zone


async def update_diagonalley_zone(zone_id: str, **kwargs) -> Optional[Zones]:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE diagonalley.zones SET {q} WHERE id = ?",
        (*kwargs.values(), zone_id),
    )
    row = await db.fetchone("SELECT * FROM diagonalley.zones WHERE id = ?", (zone_id,))
    return Zones(**row) if row else None


async def get_diagonalley_zone(zone_id: str) -> Optional[Zones]:
    row = await db.fetchone("SELECT * FROM diagonalley.zones WHERE id = ?", (zone_id,))
    return Zones(**row) if row else None


async def get_diagonalley_zones(user: str) -> List[Zones]:
    rows = await db.fetchall(
        'SELECT * FROM diagonalley.zones WHERE "user" = ?', (user,)
    )
    return [Zones(**row) for row in rows]


async def delete_diagonalley_zone(zone_id: str) -> None:
    await db.execute("DELETE FROM diagonalley.zones WHERE id = ?", (zone_id,))


###Stalls


async def create_diagonalley_stall(data: createStalls) -> Stalls:
    stall_id = urlsafe_short_hash()
    await db.execute(
        f"""
        INSERT INTO diagonalley.stalls (
            id,
            wallet,
            name,
            publickey,
            privatekey,
            relays,
            shippingzones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            stall_id,
            data.wallet,
            data.name,
            data.publickey,
            data.privatekey,
            data.relays,
            data.shippingzones,
        ),
    )

    stall = await get_diagonalley_stall(stall_id)
    assert stall, "Newly created stall couldn't be retrieved"
    return stall


async def update_diagonalley_stall(stall_id: str, **kwargs) -> Optional[Stalls]:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE diagonalley.stalls SET {q} WHERE id = ?",
        (*kwargs.values(), stall_id),
    )
    row = await db.fetchone(
        "SELECT * FROM diagonalley.stalls WHERE id = ?", (stall_id,)
    )
    return Stalls(**row) if row else None


async def get_diagonalley_stall(stall_id: str) -> Optional[Stalls]:
    row = await db.fetchone(
        "SELECT * FROM diagonalley.stalls WHERE id = ?", (stall_id,)
    )
    print("ROW", row)
    return Stalls(**row) if row else None


async def get_diagonalley_stalls(wallet_ids: Union[str, List[str]]) -> List[Stalls]:
    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"SELECT * FROM diagonalley.stalls WHERE wallet IN ({q})", (*wallet_ids,)
    )
    return [Stalls(**row) for row in rows]

async def get_diagonalley_stalls_by_ids(stall_ids: Union[str, List[str]]) -> List[Stalls]:
    q = ",".join(["?"] * len(stall_ids))
    rows = await db.fetchall(
        f"SELECT * FROM diagonalley.stalls WHERE id IN ({q})", (*stall_ids,)
    )
    return [Stalls(**row) for row in rows]    


async def delete_diagonalley_stall(stall_id: str) -> None:
    await db.execute("DELETE FROM diagonalley.stalls WHERE id = ?", (stall_id,))


###Orders


async def create_diagonalley_order(data: createOrder, invoiceid: str) -> Orders:
    returning = "" if db.type == SQLITE else "RETURNING ID"
    method = db.execute if db.type == SQLITE else db.fetchone

    result = await (method)(
        f"""
            INSERT INTO diagonalley.orders (wallet, shippingzone, address, email, total, invoiceid, paid, shipped)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            {returning}
            """,
        (
            data.wallet,
            data.shippingzone,
            data.address,
            data.email,
            data.total,
            invoiceid,
            False,
            False,
        ),
    )
    if db.type == SQLITE:
        return result._result_proxy.lastrowid
    else:
        return result[0]
    # link = await get_diagonalley_order(link.id)
    # assert link, "Newly created link couldn't be retrieved"
    # return link


async def create_diagonalley_order_details(
    order_id: str, data: List[createOrderDetails]
):
    for item in data:
        item_id = urlsafe_short_hash()
        await db.execute(
            """
            INSERT INTO diagonalley.order_details (id, order_id, product_id, quantity)
            VALUES (?, ?, ?, ?)
            """,
            (
                item_id,
                order_id,
                item.product_id,
                item.quantity,
            ),
        )
    order_details = await get_diagonalley_order_details(order_id)
    return order_details


async def get_diagonalley_order_details(order_id: str) -> List[OrderDetail]:
    rows = await db.fetchall(
        f"SELECT * FROM diagonalley.order_details WHERE order_id = ?", (order_id,)
    )

    return [OrderDetail(**row) for row in rows]


async def get_diagonalley_order(order_id: str) -> Optional[Orders]:
    row = await db.fetchone(
        "SELECT * FROM diagonalley.orders WHERE id = ?", (order_id,)
    )
    return Orders(**row) if row else None


async def get_diagonalley_order_invoiceid(invoice_id: str) -> Optional[Orders]:
    row = await db.fetchone(
        "SELECT * FROM diagonalley.orders WHERE invoiceid = ?", (invoice_id,)
    )
    return Orders(**row) if row else None


async def set_diagonalley_order_paid(payment_hash: str) -> Orders:
    await db.execute(
        """
            UPDATE diagonalley.orders
            SET paid = true
            WHERE invoiceid = ?
            """,
        (payment_hash,),
    )


async def update_diagonalley_product_stock(products):

    q = "\n".join(
        [f"""WHEN id='{p.product_id}' THEN quantity - {p.quantity}""" for p in products]
    )
    v = ",".join(["?"] * len(products))

    await db.execute(
        f"""
            UPDATE diagonalley.products
            SET quantity=(CASE
                        {q}
                        END)
            WHERE id IN ({v});
        """,
        (*[p.product_id for p in products],),
    )


async def get_diagonalley_orders(wallet_ids: Union[str, List[str]]) -> List[Orders]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"SELECT * FROM diagonalley.orders WHERE wallet IN ({q})", (*wallet_ids,)
    )
    #
    return [Orders(**row) for row in rows]


async def delete_diagonalley_order(order_id: str) -> None:
    await db.execute("DELETE FROM diagonalley.orders WHERE id = ?", (order_id,))


### Market/Marketplace


async def get_diagonalley_markets(user: str) -> List[Market]:
    rows = await db.fetchall("SELECT * FROM diagonalley.markets WHERE usr = ?", (user,))
    return [Market(**row) for row in rows]


async def get_diagonalley_market(market_id: str) -> Optional[Market]:
    row = await db.fetchone(
        "SELECT * FROM diagonalley.markets WHERE id = ?", (market_id,)
    )
    return Market(**row) if row else None


async def get_diagonalley_market_stalls(market_id: str):
    rows = await db.fetchall(
        "SELECT * FROM diagonalley.market_stalls WHERE marketid = ?", (market_id,)
    )   

    ids =  [row["stallid"] for row in rows]
    
    return await get_diagonalley_stalls_by_ids(ids)


async def create_diagonalley_market(data: CreateMarket):
    market_id = urlsafe_short_hash()

    await db.execute(
        """
            INSERT INTO diagonalley.markets (id, usr, name)
            VALUES (?, ?, ?)
            """,
        (
            market_id,
            data.usr,
            data.name,
        ),
    )
    market = await get_diagonalley_market(market_id)
    assert market, "Newly created market couldn't be retrieved"
    return market


async def create_diagonalley_market_stalls(
    market_id: str, data: List[CreateMarketStalls]
):
    for stallid in data:
        id = urlsafe_short_hash()

        await db.execute(
            """
            INSERT INTO diagonalley.market_stalls (id, marketid, stallid)
            VALUES (?, ?, ?)
            """,
            (
                id,
                market_id,
                stallid,
            ),
        )
    market_stalls = await get_diagonalley_market_stalls(market_id)
    return market_stalls


async def update_diagonalley_market(market_id):
    pass
