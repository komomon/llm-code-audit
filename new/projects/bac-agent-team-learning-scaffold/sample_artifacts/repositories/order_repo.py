def get_order(order_id):
    return db.orders.find_one({"id": order_id})


def save(order):
    return db.orders.save(order)


def delete(order):
    return db.orders.delete_one({"id": order.id})
