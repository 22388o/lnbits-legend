import asyncio

from loguru import logger

from lnbits.core.models import Payment
from lnbits.tasks import register_invoice_listener

from .crud import (
    get_shop_order_details,
    get_shop_order_invoiceid,
    set_shop_order_paid,
    update_shop_product_stock,
)


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue)

    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra and payment.extra.get("tag") != "shop":
        return

    order = await get_shop_order_invoiceid(payment.payment_hash)
    if not order:
        logger.error("this should never happen", payment)
        return

    # set order as paid
    await set_shop_order_paid(payment.payment_hash)

    # deduct items sold from stock
    details = await get_shop_order_details(order.id)
    await update_shop_product_stock(details)
