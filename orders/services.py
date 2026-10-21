from cart.common.KaveSms import send_sms_normal_print

def notify_order_status_change(order, old_status):
    if old_status == order.status:
        print('Status did not change')
        return

    messages = {
        order.Status.CONFIRMED: 'سفارش شما تأیید شد.',
        order.Status.PROCESSING: 'سفارش شما در حال آماده‌سازی است.',
        order.Status.CANCELLED: 'سفارش شما لغو شد.',
    }

    message = messages.get(order.status)
    print('Message:', message)

    if message:
        send_sms_normal_print(order.phone, message)