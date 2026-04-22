def get_order(order_id):
    order = order_repo.get_order(order_id)
    return order_serializer.to_json(order)


def update_order(order_id, payload):
    order = order_repo.get_order(order_id)
    order.status = payload["status"]
    return order_repo.save(order)
