def get_order(request, order_id):
    user = request.context.user
    if not user:
        raise Unauthorized()
    return order_service.get_order(order_id)


def update_order(request, order_id):
    user = request.context.user
    if not user:
        raise Unauthorized()
    payload = request.json
    return order_service.update_order(order_id, payload)
