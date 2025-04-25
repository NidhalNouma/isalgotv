
import datetime
import environ
env = environ.Env()

import json
import stripe
stripe.api_key = env('STRIPE_API_KEY')
stripe_wh_secret = env('STRIPE_API_WEBHOOK_SECRET')

def check_coupon_fn(coupon_id, plan_id, price, customer_id):
    # print(coupon_id, plan_id, price)
    try:
        orig_price = price

        promotion_codes = stripe.PromotionCode.list(code=coupon_id, active=True)

        # Check if any promotion codes were returned
        if not promotion_codes.data:
            # print("No promotion codes found with the given code.")
            raise Exception("No promotion codes found with the given code.")
        else:
            # Use the first matching promotion code (if multiple, adjust logic as needed)
            promo_code = promotion_codes.data[0]
                # Step 2: Validate general properties
            is_active = promo_code.active
            expires_at = promo_code.expires_at
            max_redemptions = promo_code.max_redemptions
            times_redeemed = promo_code.times_redeemed
            restrictions = promo_code.restrictions

            # Validation logic for general properties
            if not is_active:
                raise Exception("Promotion code is inactive.")
            elif expires_at and expires_at < datetime.datetime.now().timestamp():
                raise Exception("Promotion code has expired.")
            elif max_redemptions and times_redeemed >= max_redemptions:
                raise Exception("Promotion code has reached its redemption limit.")

            # Step 3: Check customer-specific restrictions
            if restrictions.get("first_time_transaction", False):
                # If first-time transaction restriction is set, check if customer has transactions
                invoices = stripe.Invoice.list(customer=customer_id)
                if any(invoice.paid for invoice in invoices.auto_paging_iter()):
                    raise Exception("Promotion code is restricted to first-time transactions, and the customer is not eligible.")
                else:
                    print("Customer is eligible under first-time transaction restriction.")

            # Step 4: Check if the customer has already used the promotion code
            invoices = stripe.Invoice.list(customer=customer_id)
            has_used_promo_code = any(
                invoice.discount and invoice.discount.promotion_code == promo_code.id
                for invoice in invoices.auto_paging_iter()
            )

            if has_used_promo_code:
                raise Exception("Customer has already used this promotion code.")

            coupon = promo_code.coupon

        promo_id = promo_code.id

        if coupon.percent_off:
            price = round(price - (price * coupon.percent_off / 100), 2)

            coupon_off = str(-coupon.percent_off) + "%"
        elif coupon.amount_off:
            price = round(price - coupon.amount_off, 2)

            coupon_off = str(-coupon.amount_off) + '$'
        
        if coupon_id.find("QUAT") >= 0 or coupon_id.find("QUAR") >= 0:
            if plan_id != "QUARTERLY":
                raise Exception("Coupon code is not valid for this plan.")
        elif coupon_id.find("MN") >= 0:
            if plan_id != "MONTHLY":
                raise Exception("Coupon code is not valid for this plan.")
        elif coupon_id.find("LIFETIME") >= 0:
            if plan_id != "LIFETIME":
                raise Exception("Coupon code is not valid for this plan.")
        if plan_id == "LIFETIME":
            if coupon_id.find("BETA") >= 0:
                price = orig_price
                raise Exception("This is a beta plan, you cannot use it on lifetime plan.")
            elif coupon_id.find("LIFETIME") < 0:
                raise Exception("Coupon code is not valid for lifetime plan.")
            
        return (price, coupon_off, promo_id)
    except Exception as e:
        # print(e)
        raise e
