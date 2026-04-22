def update_order(order_id, payload):
    order = order_repo.get_order(order_id)
    order.status = payload["status"]
    order.note = payload["note"]
    return order_repo.save(order)


def delete_order(order_id):
    order = order_repo.get_order(order_id)
    return order_repo.delete(order)
