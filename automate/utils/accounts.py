
def desactivate_account_by_subscription_id(broker_type, subscription_id):
    try:
        from automate.models import ForexBrokerAccount, CryptoBrokerAccount
        crypto_broker_types = [choice[0] for choice in CryptoBrokerAccount.BROKER_TYPES]
        forex_broker_types = [choice[0] for choice in ForexBrokerAccount.BROKER_TYPES]

        accounts = []

        if broker_type in crypto_broker_types:
            objs = CryptoBrokerAccount.objects.filter(subscription_id=subscription_id)
            for obj in objs:
                obj.deactivate()
                accounts.append(obj)

        elif broker_type in forex_broker_types:
            objs = ForexBrokerAccount.objects.filter(subscription_id=subscription_id)
            for obj in objs:
                obj.deactivate()
                accounts.append(obj)
        else:
            raise Exception("Invalid Broker Type")
        
        return accounts

    except Exception as e:
        print(e)
        raise Exception("Error desactivating account: " + str(e))