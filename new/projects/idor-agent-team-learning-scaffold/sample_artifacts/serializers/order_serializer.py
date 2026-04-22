def to_json(order):
    return {
        "id": order.id,
        "status": order.status,
        "owner_id": order.owner_id,
    }
