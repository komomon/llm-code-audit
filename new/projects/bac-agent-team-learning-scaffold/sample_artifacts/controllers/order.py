def update_order(request, order_id):
    user = request.context.user
    if not user:
        raise Unauthorized()
    payload = request.json
    return order_service.update_order(order_id, payload)


def delete_order(request, order_id):
    user = request.context.user
    if not user:
        raise Unauthorized()
    return order_service.delete_order(order_id)
