import datetime
import time
import environ
env = environ.Env()

from automate.utils.accounts import desactivate_account_by_subscription_id

from profile_user.tasks import *
from automate.tasks import *
from strategies.tasks import *

import stripe
stripe.api_key = env('STRIPE_API_KEY')
stripe_wh_secret = env('STRIPE_API_WEBHOOK_SECRET')
stripe_wh_secret_connect = env('STRIPE_API_WEBHOOK_SECRET_CONNECT')

def check_coupon_fn(user_profile, coupon_id, price):
    try:
        customer_id = user_profile.customer_id_value
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
        
        # if coupon_id.find("QUAT") >= 0 or coupon_id.find("QUAR") >= 0:
        #     if plan_id != "QUARTERLY":
        #         raise Exception("Coupon code is not valid for this plan.")
        # elif coupon_id.find("MN") >= 0:
        #     if plan_id != "MONTHLY":
        #         raise Exception("Coupon code is not valid for this plan.")
        # elif coupon_id.find("LIFETIME") >= 0:
        #     if plan_id != "LIFETIME":
        #         raise Exception("Coupon code is not valid for this plan.")
        # if plan_id == "LIFETIME":
        #     if coupon_id.find("BETA") >= 0:
        #         price = orig_price
        #         raise Exception("This is a beta plan, you cannot use it on lifetime plan.")
        #     elif coupon_id.find("LIFETIME") < 0:
        #         raise Exception("Coupon code is not valid for lifetime plan.")
            
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
        "has_subscription": False,
    }

    try:
        if user_profile.customer_id_value:
            try:
                stripe_customer = stripe.Customer.retrieve(user_profile.customer_id)
                if getattr(stripe_customer, "deleted", False):
                    print(f"Stripe customer {user_profile.customer_id} is marked as deleted.")
                    stripe_customer = None
                data["customer"] = stripe_customer
                # print("stripe customer, " , stripe_customer)
            except Exception as e:
                print("Error with getting stripe customer...", e)


        if user_profile.is_lifetime:
            data["has_subscription"] = True

        # Retrieve subscription if exists
        if user_profile.subscription_id and not user_profile.is_lifetime:
            try:
                subscription = stripe.Subscription.retrieve(user_profile.subscription_id)
                data["subscription"] = subscription
                
                if subscription.status == 'active' and subscription.current_period_end > time.time():
                    data["has_subscription"] = True
                elif subscription.status == 'trialing' and subscription.current_period_end > time.time():
                    data["has_subscription"] = True
                elif subscription.status == 'past_due' and subscription.current_period_end > time.time():
                    data["has_subscription"] = True
                elif subscription.status == "incomplete":
                    data["has_subscription"] = False

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


def get_or_create_customer_by_email(user):
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
            results = stripe.Customer.search(query=f"email:'{user.email}'", limit=1)
            if results.data:
                cust = results.data[0]
                if not getattr(cust, "deleted", False):
                    return cust, False
        except Exception:
            # Some accounts may not have search enabled; ignore and fall back.
            pass

        # 2) Fallback to list filter (case-sensitive per Stripe docs).
        candidates = stripe.Customer.list(email=user.email, limit=1)
        if candidates.data:
            cust = candidates.data[0]
            if not getattr(cust, "deleted", False):
                return cust, False

        # 3) Create if nothing matched.
        create_params = {"email": user.email}
        if user.username:
            create_params["name"] = user.username
        create_params["metadata"] = {"user_id": str(user.id)}

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

def create_user_setup_intent(user_profile, to_add = False):
    """
    Create a Stripe Setup Intent for saving payment methods.
    """
    try:
        customer_id = user_profile.customer_id_value

        payment_methods_types = ["card"]
        # if to_add:
        #     payment_methods_types.append("cashapp")

        setup_intent = stripe.SetupIntent.create(
            customer=customer_id,
            payment_method_types=payment_methods_types,
            usage="off_session",
            metadata={
                "user_id": str(user_profile.user.id),
                "profile_user_id": str(user_profile.id),
            }
        )
        return setup_intent
    except Exception as e:
        print("Error creating setup intent:", e)
        raise

def create_payment_intent(user_profile, payment_method, amount=0.0, currency="usd", description="Payment"):
    """
    Create a Stripe Payment Intent for one-time payments.
    """
    try:
        customer_id = user_profile.customer_id_value
        if not customer_id:
            raise Exception("User does not have a Stripe customer ID.")
        if amount <= 0:
            raise Exception("Amount must be greater than zero.")

        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # amount in cents
            currency=currency,
            customer=customer_id,
            payment_method=payment_method,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            description=description,
            metadata={
                "user_id": str(user_profile.user.id),
                "profile_user_id": str(user_profile.id),
            },
        )
        return payment_intent
    except Exception as e:
        print("Error creating payment intent:", e)
        raise

def create_seller_account(user, country):
    """
    Create a Stripe Seller Account.
    """
    try:
        if not country:
            raise Exception("Country is required to create a seller account. Complete your profile with your country information.")
        platform_country = "US"

        account_params = {
            "type": "express",
            "email": user.email,
            "country": country,
            "capabilities": {"transfers": {"requested": True}},
            "metadata": {
                "user_id": str(user.id),
                'profile_user_id': str(user.user_profile.id) if hasattr(user, 'user_profile') else None,
                'customer': str(user.user_profile.customer_id) if hasattr(user, 'user_profile') else None,
            },
        }

        # "recipient" ToS is only for cross-border (platform and account in different countries)
        if country.upper() != platform_country:
            account_params["tos_acceptance"] = {"service_agreement": "recipient"}

        account = stripe.Account.create(**account_params)
        return account
    except Exception as e:
        print("Error creating seller account:", e)
        raise

def delete_seller_account(account_id):
    """
    Deletes a Stripe Seller Account by its ID.
    """
    try:
        print(f"Deleting Stripe seller account {account_id}")
        stripe.Account.delete(account_id)
    except stripe.error.StripeError as e:
        # log or ignore Stripe deletion errors
        print(f"Error deleting Stripe seller account {account_id}: {e}")

def get_seller_account_link(account_id, refresh_url, return_url):
    """
    Create a Stripe Account Link for onboarding or managing a Seller Account.
    """
    try:
        account_link_obj = stripe.AccountLink.create(
            account=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type='account_onboarding',
        )
        return account_link_obj
    except Exception as e:
        print("Error creating seller account link:", e)
        raise

def get_seller_login_link(account_id):
    """
    Create a Stripe Login Link for a Seller Account.
    """
    try:
        login_link_obj = stripe.Account.create_login_link(account_id)
        return login_link_obj
    except Exception as e:
        print("Error creating seller login link:", e)
        raise

def get_seller_account(account_id):
    """
    Retrieve a Stripe Seller Account by its ID.
    Returns the full Account object.
    """
    try:
        account = stripe.Account.retrieve(account_id)
        print(f"Retrieved seller account: {account.id} - {account.email}")
        return account
    except Exception as e:
        # Re-raise to be handled by the caller
        raise

def create_strategy_price(strategy, strategy_price) -> (tuple):
    """
    Create a Stripe Price for a given strategy.
    """
    try:
        product_id = strategy_price.stripe_product_id
        profile_user = strategy.created_by.user_profile

        if not product_id:
            product = stripe.Product.create(
                name=strategy.name,
                description=strategy.description,
                metadata={
                    "strategy_id": str(strategy.id),
                    "created_by": strategy.created_by.username,
                    "account_id": str(profile_user.get_seller_account_id()),
                }
            )
            product_id = product.id
        else:
            product = stripe.Product.retrieve(product_id)

            availble_prices = stripe.Price.list(product=product_id)
            price_exists =  next(p for p in availble_prices.auto_paging_iter() if p.recurring and p.recurring.interval == strategy_price.interval and p.recurring.interval_count == strategy_price.interval_count and p.unit_amount == int(strategy_price.amount * 100))
            if price_exists:
                return product, price_exists
        


        price = stripe.Price.create(
            unit_amount=int(strategy_price.amount * 100),  # amount in cents
            currency="usd",
            product=product_id,
            recurring={"interval": strategy_price.interval, "interval_count": strategy_price.interval_count},
            metadata={
                "strategy_id": str(strategy.id),
                "created_by": strategy.created_by.username,
                "account_id": str(profile_user.get_seller_account_id()),
            }
        )

        return product, price

    except Exception as e:
        print("Error creating strategy price:", e)
        raise

def subscription_object(subscription=None, subscription_id=None):
    try:
        if not subscription and not subscription_id:
            return None

        if not subscription and subscription_id:
            subscription = stripe.Subscription.retrieve(id=subscription_id)

        if subscription.get('status') not in ["active", "trialing", "past_due"]:
            return None

        if subscription.get('__active__', False):
            return subscription
        sub = {
            "__active__": subscription.get('status') in ["active", "trialing"],
            "id": subscription.get('id'),
            "status": subscription.get('status'),
            "period_start": datetime.datetime.fromtimestamp(subscription.get("current_period_start", 0)),
            "period_end": datetime.datetime.fromtimestamp(subscription.get("current_period_end", 0)),
            "cancel_at_period_end": subscription.get("cancel_at_period_end"),
            "price_id": subscription.get("plan", {}).get("id"),
            "product_id": subscription.get("plan", {}).get("product"),
            "interval": subscription.get("plan", {}).get("interval"),
            "interval_count": subscription.get("plan", {}).get("interval_count"),
            "amount": subscription.get("plan", {}).get("amount", 0) / 100,
            "currency": subscription.get("plan", {}).get("currency"),
            "payment_method": subscription.get("default_payment_method"),
            "is_paused": subscription.get("pause_collection") is not None,
        }
        
        plan = str(sub.get('interval')).upper() + "LY"
        sub['plan'] = plan

        # if subscription.get('status') in ["active", "trialing"]:
        #     next_invoice = stripe.Invoice.upcoming(customer=subscription.get("customer"), subscription=subscription.get("id"))
        #     if next_invoice:
        #         sub['next_payment_amount'] = next_invoice.get("amount_due", 0) / 100

        return sub
    except Exception as e:
        print("Error processing subscription object:", e)
        return None

def subscribe_to_strategy(user_profile, strategy_price, payment_method, promotion_code=None) -> (tuple):
    """
    Subscribe a user to a strategy using Stripe.
    """
    try:
        customer_id = user_profile.customer_id_value
        price = stripe.Price.retrieve(strategy_price.stripe_price_id)
        seller_account = price.metadata.get("account_id")

        try:
            customer, user_profile = set_user_default_payment_method(user_profile, payment_method, force=True) 
        except Exception as e:
            print("Error setting default payment method:", e)
            raise

        subscription_params = {
            "customer": customer_id,
            "items": [{"price": strategy_price.stripe_price_id}],
            "application_fee_percent": 20.0,  # Platform takes 20% fee
            "transfer_data": {
                "destination": seller_account,
            },
            "expand": ["latest_invoice.payment_intent"],
            "default_payment_method": payment_method,
            "payment_behavior": "error_if_incomplete",
            "trial_settings": {"end_behavior": {"missing_payment_method": "pause"}},
            "metadata": {
                "user_id": str(user_profile.user.id),
                "profile_user_id": str(user_profile.id), 
                "strategy_id": str(strategy_price.strategy.id),
                "type": "strategy_subscription",
            },
            "description": f"Subscription for {strategy_price.strategy.name}",
        }

        if promotion_code:
            subscription_params["promotion_code"] = promotion_code

        subscription = stripe.Subscription.create(**subscription_params)

        if subscription.status in ['active', 'trialing']:
            user_profile.give_tradingview_access(strategy_price.strategy.id, access=True)

        user_profile = user_profile.get_with_update_stripe_data(True)
        return subscription, user_profile

    except Exception as e:
        print("Error subscribing to strategy:", e)
        raise

def subscribe_to_account(user_profile, broker_account, price_id, payment_method, promotion_code=None) -> (tuple):
    """
    Subscribe a user to a broker account using Stripe.
    """
    try:
        customer_id = user_profile.customer_id_value

        try:
            customer, user_profile = set_user_default_payment_method(user_profile, payment_method, force=True) 
        except Exception as e:
            print("Error setting default payment method:", e)
            raise

        subscription_params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "expand": ["latest_invoice.payment_intent"],
            "default_payment_method": payment_method,
            "payment_behavior": "error_if_incomplete",
            "trial_settings": {"end_behavior": {"missing_payment_method": "pause"}},
            "metadata": {
                "user_id": str(user_profile.user.id),
                "profile_user_id": str(user_profile.id), 
                "broker_type": broker_account.broker_type,
                "type": 'account_subscription',
            },
            "description": f"Subscription for {broker_account.name}",
        }

        if promotion_code:
            subscription_params["promotion_code"] = promotion_code

        subscription = stripe.Subscription.create(**subscription_params)

        user_profile = user_profile.get_with_update_stripe_data(True)
        return subscription, user_profile

    except Exception as e:
        print("Error subscribing to broker account:", e)
        raise

def subscribe_to_main_membership(user_profile, price_id, payment_method, free_trial_days=0, promo_id=None, is_lifetime={}) -> (tuple):
    """
    Subscribe a user to the main membership using Stripe.
    """
    try:
        customer_id = user_profile.customer_id_value
        old_subscription_id = user_profile.subscription_id

        old_subscription = subscription_object(None, old_subscription_id)
        old_subscription_deleted = False

        try:
            customer, user_profile = set_user_default_payment_method(user_profile, payment_method, force=True) 
        except Exception as e:
            print("Error setting default payment method:", e)
            raise

        if is_lifetime and is_lifetime.get('is_lifetime', False):
            lifetime_intent = create_payment_intent(
                user_profile=user_profile,
                payment_method=payment_method,
                amount=is_lifetime.get('price', 0),
                currency=is_lifetime.get('currency', 'usd'),
                description=is_lifetime.get('description', 'Lifetime subscription.')
            )
            user_profile.lifetime_intent = lifetime_intent.id
            user_profile.is_lifetime = True
            user_profile.save()

            if old_subscription:
                try:
                    stripe.Subscription.delete(old_subscription_id)
                    old_subscription_deleted = True
                except Exception as e:
                    print("Error deleting old subscription:", e)

            user_profile = user_profile.get_with_update_stripe_data(True)

            return lifetime_intent, old_subscription_deleted, user_profile

        trial_end = 'now'
        if int(free_trial_days) > 0 and not old_subscription:
            trial_end = int((datetime.datetime.now() + datetime.timedelta(days=free_trial_days)).timestamp())
        elif old_subscription and old_subscription.get('period_end'):
            # If user has an old subscription with remaining trial, preserve it
            now = datetime.datetime.now()
            if old_subscription['period_end'] > now:
                trial_end = int(old_subscription['period_end'].timestamp())

        subscription_params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "expand": ["latest_invoice.payment_intent"],
            "default_payment_method": payment_method,
            "payment_behavior": "error_if_incomplete",
            "metadata": {
                "user_id": str(user_profile.user.id),
                "profile_user_id": str(user_profile.id), 
                "type": "main_membership",
            },
            "description": f"Subscription for main membership",
            "trial_end": trial_end,
            "trial_settings": {"end_behavior": {"missing_payment_method": "pause"}},
        }

        if promo_id:
            subscription_params["promotion_code"] = promo_id

        subscription = stripe.Subscription.create(**subscription_params)

        user_profile.subscription_id = subscription.id
        user_profile.save()

        if old_subscription:
            try:
                stripe.Subscription.delete(old_subscription_id)
                old_subscription_deleted = True
            except Exception as e:
                print("Error deleting old subscription:", e)

        user_profile = user_profile.get_with_update_stripe_data(True)
        return subscription, old_subscription_deleted, user_profile

    except Exception as e:
        print("Error subscribing to main membership:", e)
        raise

def cancel_reactivate_subscription(user_profile, subscription_id) -> (tuple):
    """
    Cancel a user's strategy subscription at period end.
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        cancel_active = subscription.cancel_at_period_end
        
        if subscription.status not in ["active", "trialing"]:
            raise Exception("Canceled subscriptions cannot be reactivated. Create a new subscription.")


        canceled_subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=not cancel_active,
        )

        user_profile = user_profile.get_with_update_stripe_data(True)

        return subscription_object(canceled_subscription), user_profile

    except Exception as e:
        print("Error canceling subscription:", e)
        raise

def pause_unpause_subscription(user_profile, subscription_id) -> (tuple):
    """
    Pause or unpause a user's strategy subscription.
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        if subscription.status == "incomplete":
            raise Exception("Incomplete subscriptions cannot be paused. Please complete the subscription first.")
        
        pause_active = subscription.pause_collection is None

        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            pause_collection={"behavior": "mark_uncollectible"} if pause_active else "",
        )

        # user_profile = user_profile.get_with_update_stripe_data(True)

        return subscription_object(updated_subscription), user_profile

    except Exception as e:
        print("Error pausing/unpausing subscription:", e)
        raise

def change_subscription_payment_method(user_profile, subscription_id, payment_method) -> (tuple):
    """
    Change the payment method for a user's subscription.
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)

        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            default_payment_method=payment_method,
        )
        
        user_profile = user_profile.get_with_update_stripe_data(True)

        return subscription_object(updated_subscription), user_profile

    except Exception as e:
        print("Error changing subscription payment method:", e)
        raise

def get_payment_method_details(payment_method_id):
    """
    Retrieve details of a payment method by its ID.
    """
    try:
        payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
        return payment_method
    except Exception as e:
        print("Error retrieving payment method details:", e)
        raise

def add_user_payment_method(user_profile, payment_method, set_to_default=False) -> (tuple):
    try:
        customer_id = user_profile.customer_id_value
        stripe.PaymentMethod.attach(
                payment_method,
                customer=customer_id,
            )
        if set_to_default:
            stripe.Customer.modify(
                    customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method
                    }
                )
        
        user_profile = user_profile.get_with_update_stripe_data(True)
        payment_methods = user_profile.stripe_obj.get('payment_methods', None)

        return payment_methods, user_profile
        
    
    except Exception as e:
        print("Error adding payment method:", e)
        raise

def delete_user_payment_method(user_profile, payment_method) -> (tuple):
    try:
        customer_id = user_profile.customer_id_value
        subscriptions = stripe.Subscription.list(customer=customer_id, status="all")

        filterd_subs = [sub for sub in subscriptions.auto_paging_iter() if sub.status in ['active', 'trialing', 'past_due']]

        # Check if the payment method is used in any active subscription
        for subscription in filterd_subs:
            if subscription.default_payment_method == payment_method:
                raise Exception("This payment method is currently associated with an active subscription and cannot be deleted.")

        
        stripe.PaymentMethod.detach(payment_method)
        user_profile = user_profile.get_with_update_stripe_data(force = True)
        payment_methods = user_profile.stripe_obj.get('payment_methods', None)
        # payment_methods = stripe.Customer.list_payment_methods(customer_id)

        return payment_methods, user_profile

    except Exception as e:
        print("Error deleting payment method:", e)
        raise
        
def set_user_default_payment_method(user_profile, payment_method, force=False) -> (tuple):
    try:
        customer_id = user_profile.customer_id_value

        customer = stripe.Customer.retrieve(customer_id)
        should_update = (
            (force and not customer.invoice_settings.default_payment_method)
            or (not force and customer.invoice_settings.default_payment_method != payment_method)
        )

        if should_update:
            customer = stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method
                }
            )    

        if force:
            return customer, user_profile
        else:
            user_profile = user_profile.get_with_update_stripe_data(force = True)
            return customer, user_profile

    except Exception as e:
        print("Error setting default payment method:", e)
        raise

def is_customer_subscribed_to_price(customer_id, price_id) -> (tuple):
    subscriptions = stripe.Subscription.list(
        customer=customer_id,
        price=price_id,
        status="all",
    )

    for sub in subscriptions.data:
        if sub.status not in ["active", "trialing", "past_due"]:
            continue

        for item in sub["items"]["data"]:
            if item["price"]["id"] == price_id:
                return True, subscription_object(sub)

    return False, None

def is_customer_subscribed_to_product(customer_id, product_id) -> (tuple):
    subscriptions = stripe.Subscription.list(
        customer=customer_id,
        status="all",
    )

    for sub in subscriptions.data:
        if sub.status not in ["active", "trialing", "past_due"]:
            continue

        for item in sub["items"]["data"]:
            if item["price"]["product"] == product_id:
                return True, subscription_object(sub)

    return False, None

def send_money_to_seller_account(amount, destination_account_id, description="Payout to seller", currency="usd"):
    """
    Send money to a connected Stripe seller account.
    """
    try:
        transfer = stripe.Transfer.create(
            amount=int(amount * 100),  # amount in cents
            currency=currency,
            destination=destination_account_id,
            description=description,
        )
        return transfer
    except Exception as e:
        print("Error sending money to seller account:", e)
        raise

def product_overview(product_id, price_id):
    try:
        product = stripe.Product.retrieve(product_id)
        price = stripe.Price.retrieve(price_id)
        
        amount = price.unit_amount / 100
        interval = price.recurring["interval"]
        interval_count = price.recurring["interval_count"]
        currency = price.currency

        product.price_overview = {
            "amount": amount,   
            "interval": interval,
            "interval_count": interval_count,
            "currency": currency,
        }

        return product
    except Exception as e:
        print("Error retrieving subscription overview:", e)
        raise


def handle_webhook_event(User_Profile, Strategy, StrategySubscriber, event):
    try:
        if event['type'] == 'customer.deleted':
            customer = event['data']['object']
            customer_id = customer.get("id")
            user_profile = User_Profile.objects.filter(customer_id=customer_id).first()
            if user_profile:
                user_profile.customer_id = ""
                user_profile.subscription_id = ""
                user_profile.get_with_update_stripe_data(force=True)
                user_profile.save()
                print("Stripe-Webhook: Customer deleted, user profile updated ... ", "customer_id:", customer_id, "user_profile_id:", user_profile.id)
                return {
                    "status": "success",
                    "message": "Customer deleted, user profile updated.",
                    "user_profile_id": user_profile.id,
                }
            else:
                print("Stripe-Webhook: User profile not found for customer deletion ... ", "customer_id:", customer_id)
                return {
                    "status": "ignored",
                    "reason": "User profile not found for customer deletion",
                }

        elif event['type'] == 'account.updated':
            account = event['data']['object']
            if account:
                account_id = account.get("id")
                account_metadata = account.get("metadata", {})
                charges_enabled = account.get("charges_enabled", False)
                payout_enabled = account.get("payouts_enabled", False)

                user_profile = User_Profile.objects.filter(seller_account_id=account_id).first()
                if user_profile:
                    if charges_enabled:
                        if not user_profile.seller_account_verified:
                            send_seller_account_verified_email_task(user_profile.user.email)
                    if not charges_enabled or not payout_enabled:
                        print("Stripe-Webhook: Seller account disabled ... ", "charges_enabled:", charges_enabled, "payouts_enabled:", payout_enabled, "account_id:", account_id)
                    elif charges_enabled and payout_enabled:
                        print("Stripe-Webhook: Seller account enabled ... ", "charges_enabled:", charges_enabled, "payouts_enabled:", payout_enabled, "account_id:", account_id)
                    user_profile.verify_seller_account(charges_enabled=charges_enabled, payouts_enabled=payout_enabled)
                        

                    return {
                        "status": "success",
                        "message": "Account updated, user profile verified.",
                        "charges_enabled": charges_enabled,
                        "payouts_enabled": payout_enabled,
                        "user_profile_id": user_profile.id,
                    }

                else:
                    print("Stripe-Webhook: User profile not found for account update ... ", "account_id:", account_id)
                    return {
                        "status": "ignored",
                        "reason": "User profile not found for account update",
                    }

            print("Stripe-Webhook: Account updated event received without account object ...")
            return {
                "status": "ignored",
                "reason": "No account object in event data",
            }
        
                
        elif event['type'] == 'invoice.payment_failed':
            print("Stripe-Webhook: Payment failed, subscription marked as past due ...")
            invoice = event['data']['object']

            subscription_id = invoice.get("subscription")
            if subscription_id:
                sub_metadata = invoice.get("subscription_details", {}).get("metadata", {})
                
                user_profile_id = sub_metadata.get('profile_user_id', 0)
                type = sub_metadata.get('type', '')

                if not user_profile_id or not type:
                    print("Stripe-Webhook: Missing metadata, ignoring event ...")
                    return {
                        "status": "ignored",
                        "reason": "Missing metadata",
                    }
                
                if type not in ["account_subscription", "strategy_subscription", "main_membership"]:
                    print("Stripe-Webhook: Unrecognized subscription type, ignoring event ...")
                    return {
                        "status": "ignored",
                        "reason": "Unrecognized subscription type",
                    }
                
                user_profile = None
                try:
                    user_profile = User_Profile.objects.get(id=int(user_profile_id))
                except Exception as e:
                    pass

                if not user_profile:
                    print("Stripe-Webhook: User profile not found, ignoring event ...")
                    return {
                        "status": "ignored",
                        "reason": "User profile not found",
                    }
                
                if type == "main_membership":
                    print("Stripe-Webhook: Main membership subscription payment failed ...")

                    if user_profile.subscription_id == subscription_id:
                        user_profile.remove_access()
                        # send an email to user to notify them about the failed payment and access removal
                        overdue_access_removed_email_task(user_profile.user.email)
                    return {
                        "status": "success",
                        "message": "Main membership subscription payment failed, access removed if subscription ID matched.",
                        "user_profile_id": user_profile.id,
                    }
                elif type == "account_subscription":
                    broker_type = sub_metadata.get('broker_type', None)

                    if not broker_type:
                        print("Stripe-Webhook: Missing broker type in metadata, ignoring event ...")
                        return {
                            "status": "ignored",
                            "reason": "Missing broker type in metadata",
                            "user_profile_id": user_profile.id,
                        }

                    accounts = desactivate_account_by_subscription_id(broker_type, subscription_id)
                    # send an email to user to notify them about the failed payment and access removal
                    for account in accounts:
                        send_broker_account_access_expiring_task(user_profile.user.email, account)

                    return {
                        "status": "success",
                        "message": "Account subscription payment failed, user notified if subscription ID matched.",
                        "user_profile_id": user_profile.id,
                    }
                elif type == "strategy_subscription":
                    strategy_id = sub_metadata.get('strategy_id', 0)
                    try:
                        strategy = Strategy.objects.get(id=strategy_id)
                        if not strategy:
                            raise Exception("Strategy not found for strategy subscription payment failure.")
                        user_profile.give_tradingview_access(strategy_id=strategy_id, access=False, strategy=strategy)
                        # send an email to user to notify them about the failed payment and access removal
                        send_strategy_access_expiring_email_task(user_profile.user.email, strategy)
                    except Exception as e:
                        print("Stripe-Webhook: Strategy not found for strategy subscription payment failure, ignoring event ...")
                        return {
                            "status": "ignored",
                            "reason": str(e),
                            "user_profile_id": user_profile.id,
                        }

                    return {
                        "status": "success",
                        "message": "Strategy subscription payment failed, access removed if subscription ID matched.",
                        "user_profile_id": user_profile.id,
                    }


        elif event['type'] == 'customer.subscription.deleted' or event['type'] == 'customer.subscription.updated':

            subscription = event['data']['object']
            metadata = event['data']['object']['metadata']

            if not metadata:
                print("Stripe-Webhook: No metadata found, ignoring event ...")
                return {
                    "status": "ignored",
                    "reason": "No metadata found",
                }

            profile_user_id = metadata.get('profile_user_id', 0)
            type = metadata.get('type', '')

            if not profile_user_id or not type:
                print("Stripe-Webhook: Missing metadata, ignoring event ...")
                return {
                    "status": "ignored",
                    "reason": "Missing metadata",
                }
            
            if type not in ["account_subscription", "strategy_subscription", "main_membership"]:
                print("Stripe-Webhook: Unrecognized subscription type, ignoring event ...")
                return {
                    "status": "ignored",
                    "reason": "Unrecognized subscription type",
                }
            
            user_profile = None
            try:
                user_profile = User_Profile.objects.get(id=int(profile_user_id))
            except Exception as e:
                pass
            
            if not user_profile:
                print("Stripe-Webhook: User profile not found, ignoring event ...")
                return {
                    "status": "ignored",
                    "reason": "User profile not found",
                }

            if type == "main_membership":
                if event['type'] == 'customer.subscription.deleted':
                    print("Stripe-Webhook: Main membership subscription deleted ...")
                    if user_profile.subscription_id == subscription.id and not user_profile.is_lifetime:
                        user_profile.remove_access()
                        access_removed_email_task(user_profile.user.email)

                        return {
                            "status": "success",
                            "message": "Main membership subscription deleted, access removed.",
                            "user_profile_id": user_profile.id,
                        }
                    return {
                        "status": "success",
                        "message": "Main membership subscription deleted, but subscription ID did not match user profile, no access removed.",
                        "user_profile_id": user_profile.id,
                    }
                
                elif event['type'] == 'customer.subscription.updated':
                    print("Stripe-Webhook: Main membership subscription updated ...")

                    if subscription.status == "canceled":
                        if user_profile.subscription_id == subscription.id and not user_profile.is_lifetime:
                            user_profile.remove_access()
                            access_removed_email_task(user_profile.user.email)
                            return {
                                "status": "success",
                                "message": "Main membership subscription updated, access removed if subscription status is canceled.",
                                "user_profile_id": user_profile.id,
                            }
                        return {
                            "status": "success",
                            "message": "Main membership subscription updated, but subscription ID did not match user profile, no access removed.",
                            "user_profile_id": user_profile.id,
                        }
                    elif subscription.status == "past_due":
                        if user_profile.subscription_id == subscription.id and not user_profile.is_lifetime:
                            user_profile.remove_access()
                            # send an email to user to notify them about the failed payment and access removal
                            overdue_access_removed_email_task(user_profile.user.email)
                            return {
                                "status": "success",
                                "message": "Main membership subscription updated, access removed if subscription status is canceled or past due.",
                                "user_profile_id": user_profile.id,
                            }
                        return {
                            "status": "success",
                            "message": "Main membership subscription updated, but subscription ID did not match user profile, no access removed.",
                            "user_profile_id": user_profile.id,
                        }
                print("Stripe-Webhook: Unrecognized subscription update type, ignoring event ...")
                return {
                    "status": "passed",
                    "reason": "Unrecognized subscription update type for main membership",
                    "user_profile_id": user_profile.id,
                }
                        

            elif type == "account_subscription":
                broker_account_type = metadata.get('broker_type', '')
                if not broker_account_type:
                    print("Stripe-Webhook: Missing broker account type in metadata, ignoring event ...")
                    return {
                        "status": "ignored",
                        "reason": "Missing broker account type in metadata",
                        "user_profile_id": user_profile.id,
                    }

                if event['type'] == 'customer.subscription.deleted':
                    print("Stripe-Webhook: Account subscription deleted ...")

                    accounts = desactivate_account_by_subscription_id(broker_account_type, subscription.id)
                    # send an email to user to notify them about the subscription cancellation and access removal

                    for account in accounts:
                        send_broker_account_access_removed_task(user_profile.user.email, account=account)
                    
                    return {
                        "status": "success",
                        "message": "Account subscription deleted, user notified.",
                        "user_profile_id": user_profile.id,
                    }
                
                elif event['type'] == 'customer.subscription.updated':
                    print("Stripe-Webhook: Account subscription updated ...")

                    if subscription.status == "canceled":
                        accounts = desactivate_account_by_subscription_id(broker_account_type, subscription.id)
                        for account in accounts:
                            send_broker_account_access_removed_task(user_profile.user.email, account=account)
                        return {
                            "status": "success",
                            "message": "Account subscription updated, user notified if subscription status is canceled.",
                            "user_profile_id": user_profile.id,
                        }
                    
                    elif subscription.status == "past_due":
                        accounts = desactivate_account_by_subscription_id(broker_account_type, subscription.id)
                        for account in accounts:
                            send_broker_account_access_expiring_task(user_profile.user.email, account)

                        return {
                            "status": "success",
                            "message": "Account subscription updated, user notified if subscription status is canceled or past due.",
                            "user_profile_id": user_profile.id,
                        }
                    
                print("Stripe-Webhook: Unrecognized subscription update type, ignoring event ...")
                return {
                    "status": "passed",
                    "reason": "Unrecognized subscription update type for account subscription",
                    "user_profile_id": user_profile.id,
                }

            elif type == "strategy_subscription":
                print("Stripe-Webhook: Strategy subscription updated ...")
                
                strategy_id = metadata.get('strategy_id', 0)
                if not strategy_id:
                    print("Stripe-Webhook: Missing strategy ID in metadata, ignoring event ...")
                    return {
                        "status": "ignored",
                        "reason": "Missing strategy ID in metadata",
                    }
                try:
                    strategy = Strategy.objects.get(id=strategy_id)
                except Strategy.DoesNotExist:
                    print("Stripe-Webhook: Strategy not found, ignoring event ...")
                    return {
                        "status": "ignored",
                        "reason": "Strategy not found for strategy subscription event",
                    }

                if event['type'] == 'customer.subscription.deleted':
                    user_profile.give_tradingview_access(strategy_id=strategy_id, access=False, strategy=strategy)
                    # send an email to user to notify them about the subscription cancellation and access removal
                    send_strategy_lost_email_task(user_profile.user.email, strategy)
                    StrategySubscriber.objects.filter(user_profile=user_profile, strategy=strategy).update(active=False)
                    return {
                        "status": "success",
                        "message": "Strategy subscription deleted, access removed.",
                        "user_profile_id": user_profile.id,
                    }
                elif event['type'] == 'customer.subscription.updated':

                    if subscription.status == "canceled":
                        user_profile.give_tradingview_access(strategy_id=strategy_id, access=False, strategy=strategy)
                        # send an email to user to notify them about the subscription cancellation and access removal
                        send_strategy_lost_email_task(user_profile.user.email, strategy)
                        StrategySubscriber.objects.filter(user_profile=user_profile, strategy=strategy).update(active=False)
                        return {
                            "status": "success",
                            "message": "Strategy subscription updated, access removed if subscription status is canceled.",
                            "user_profile_id": user_profile.id,
                        }
                    
                    
                    elif subscription.status == "past_due":
                        user_profile.give_tradingview_access(strategy_id=strategy_id, access=False, strategy=strategy)
                        # send an email to user to notify them about the failed payment and access removal
                        send_strategy_access_expiring_email_task(user_profile.user.email, strategy)

                        return {
                            "status": "success",
                            "message": "Strategy subscription updated, access removed if subscription status is past due.",
                            "user_profile_id": user_profile.id,
                        }
                    
                    
                print("Stripe-Webhook: Unrecognized subscription update type, ignoring event ...")
                return {
                    "status": "passed",
                    "reason": "Unrecognized subscription update type for strategy subscription",
                    "user_profile_id": user_profile.id,
                }
                    

        print('Unhandled event type {}'.format(event['type']))
        return {
            "status": "passed",
            "reason": f"Unhandled event type {event['type']}",
        }

    except Exception as e:
        print("Error handling webhook event:", e)
        raise

def handle_stripe_webhook(User_Profile, Strategy, StrategySubscriber, payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_wh_secret
        )

        return handle_webhook_event(User_Profile, Strategy, StrategySubscriber, event)

  
    except ValueError as e:
        # Invalid payload
        print("Invalid payload")
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("Invalid signature")
        raise e
    except Exception as e:
        print("Error handling webhook:", e)
        raise e


def handle_stripe_webhook_connect(User_Profile, Strategy, StrategySubscriber, payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_wh_secret_connect
        )

        return handle_webhook_event(User_Profile, Strategy, StrategySubscriber, event)

    except ValueError as e:
        # Invalid payload
        print("Invalid payload")
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("Invalid signature")
        raise e
    except Exception as e:
        print("Error handling webhook:", e)
        raise e
