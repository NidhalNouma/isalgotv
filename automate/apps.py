from django.apps import AppConfig

class AutomateConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automate'


    def ready(self):
        import automate.signals
        import automate.signals_accounts
        
        # Initialize cTrader connection manager at startup
        # This starts the reactor and connection asynchronously
        # so it's ready when the first request comes in
        try:
            from automate.functions.brokers.ctrader import get_connection_manager
            get_connection_manager()
            print(" cTrader connection manager initialized at startup")
        except Exception as e:
            print(f" Warning: Could not initialize cTrader connection manager: {e}")
