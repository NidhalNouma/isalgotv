

import datetime
import time
import environ
env = environ.Env()

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


# Helper function to retrieve a Stripe Price by ID
def get_price_by_id(price_id):
    """
    Retrieve a Stripe Price object by its ID.
    Returns the full Price object.
    """
    try:
        price = stripe.Price.retrieve(price_id)
        # Calculate amount and remove trailing .0 if present
        amount = price.unit_amount / 100
        if isinstance(amount, float) and amount.is_integer():
            amount = int(amount)
        print(f"Retrieved price: {price.id} - {amount} {price.currency.upper()}")
        return amount
    except Exception as e:
        # Re-raise to be handled by the caller
        raise


def get_profile_data(user_profile, PRICE_LIST):

    data = {
        "customer": None,
        "subscription": None,
        "payment_methods": None,
        "payment_intent": None,
        "subscription_canceled": False,
        "subscription_next_payment_amount": None,
        "subscription_period_end": None,
        "subscription_active": False,
        "subscription_status": None,
        "subscription_price_id": None,
        "subscription_product_id": None,
        "subscription_interval": None,
        "subscription_interval_count": None,
        "subscription_plan": None,
        "has_subscription": False,
    }


    try:
        if user_profile.customer_id:
            try:
                stripe_customer = stripe.Customer.retrieve(user_profile.customer_id)
                # print("stripe customer, " , stripe_customer)
            except Exception as e:
                print("Error with getting stripe customer...", e)

        if not user_profile.customer_id or not stripe_customer or "deleted" in stripe_customer:
            customer, created = get_or_create_customer_by_email(user_profile.user.email, name=user_profile.user.username, metadata={"user_id": user_profile.user.id})

            if customer.id:
                stripe_customer = customer
                # user_profile = User_Profile.objects.get(user=current_user)
                user_profile.customer_id = customer.id
                user_profile.save(update_fields=["customer_id"])

        data["customer"] = stripe_customer

        if user_profile.is_lifetime:
            data["has_subscription"] = True

        # Retrieve subscription if exists
        if user_profile.subscription_id and not user_profile.is_lifetime:
            try:
                subscription = stripe.Subscription.retrieve(user_profile.subscription_id)
                data["subscription"] = subscription


                end_timestamp = subscription.current_period_end * 1000
                end_time = datetime.datetime.fromtimestamp(end_timestamp / 1e3)


                subscription_status = subscription.status

                subscription_interval = subscription.plan.interval
                subscription_interval_count = subscription.plan.interval_count


                data["subscription_period_end"] = end_time.isoformat()
                data["subscription_active"] = subscription.plan.active
                data["subscription_status"] = subscription.status
                data["subscription_price_id"] = subscription.plan.id
                data["subscription_product_id"] = subscription.plan.product
                data["subscription_interval"] = subscription.plan.interval
                data["subscription_interval_count"] = subscription.plan.interval_count


                if subscription_interval == "year":
                    subscription_plan = list(PRICE_LIST.keys())[2]

                elif subscription_interval == "month":
                    if subscription_interval_count == 1:
                        subscription_plan = list(PRICE_LIST.keys())[0]
                    elif subscription_interval_count == 3:
                        subscription_plan = list(PRICE_LIST.keys())[1]
                    elif subscription_interval_count == 12:
                        subscription_plan = list(PRICE_LIST.keys())[2]
                
                data["subscription_plan"] = subscription_plan
                


                if subscription_status == 'active' and subscription.current_period_end > time.time():
                    data["has_subscription"] = True
                elif subscription_status == 'trialing' and subscription.current_period_end > time.time():
                    data["has_subscription"] = True
                elif subscription_status == 'past_due' and subscription.current_period_end > time.time():
                    data["has_subscription"] = True
                # elif subscription.status == "canceled" and subscription.current_period_end > time.time():
                #     has_subscription = True
                elif subscription_status == "incomplete":
                    data["has_subscription"] = False

                
                if subscription.cancel_at_period_end or subscription.status == "canceled" or subscription.status == "incomplete":
                    data["subscription_canceled"] = True

                
                if not data["subscription_canceled"] and data["has_subscription"]:
                    # Get the upcoming invoice for the subscription
                    upcoming_invoice = stripe.Invoice.upcoming(subscription=subscription)
                    data["payment_intent"] = upcoming_invoice

                    if upcoming_invoice:
                        total_amount_due = upcoming_invoice["amount_due"]/100
                        data["subscription_next_payment_amount"] = total_amount_due
            except Exception as e:
                print("Error with getting stripe subscription...", e)


        if user_profile.customer_id:
            try:
                payment_methods = stripe.Customer.list_payment_methods(user_profile.customer_id, limit=100)
                payment_methods = payment_methods.data
                data["payment_methods"] = payment_methods
            except Exception as e:
                print("Error with getting payment methods ...", e)

    except Exception as e:
        print("Error with getting stripe data ...", e)

    return data


def get_or_create_customer_by_email(email: str, name: str | None = None, metadata: dict | None = None):
    """
    Retrieve an existing Stripe Customer by email; if none exists, create one.

    Returns:
        (customer, created)
        - customer: the Stripe Customer object
        - created: bool indicating whether a new Customer was created

    Notes:
      * We first try Stripe's Customer Search API, which supports flexible queries.
      * If search returns nothing (or is unavailable), we fall back to the
        `stripe.Customer.list(email=...)` filter.
      * We skip any objects marked as `deleted`.
    """
    try:
        # 1) Prefer the Search API (fast/flexible). Don’t use for read-after-write,
        # but we’re only reading here so it’s fine.
        try:
            results = stripe.Customer.search(query=f"email:'{email}'", limit=1)
            if results.data:
                cust = results.data[0]
                if not getattr(cust, "deleted", False):
                    return cust, False
        except Exception:
            # Some accounts may not have search enabled; ignore and fall back.
            pass

        # 2) Fallback to list filter (case-sensitive per Stripe docs).
        candidates = stripe.Customer.list(email=email, limit=1)
        if candidates.data:
            cust = candidates.data[0]
            if not getattr(cust, "deleted", False):
                return cust, False

        # 3) Create if nothing matched.
        create_params = {"email": email}
        if name:
            create_params["name"] = name
        if metadata:
            create_params["metadata"] = metadata

        customer = stripe.Customer.create(**create_params)
        return customer, True

    except Exception as e:
        # Bubble up so the caller can handle/log it
        raise

def delete_customer(user_profile):
    """
    Deletes the Stripe customer associated with the user profile.
    """
    if user_profile.customer_id:
        try:
            print(f"Deleting Stripe customer {user_profile.customer_id} for user {user_profile.user.email}")
            stripe.Customer.delete(user_profile.customer_id)
        except stripe.error.StripeError as e:
            # log or ignore Stripe deletion errors
            print(f"Error deleting Stripe customer {user_profile.customer_id}: {e}")