from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'www', 'etradingview.urls', name='www'),
    host(r'webhook', 'automate.webhook_urls', name='webhook'),
    host(r'saro', 'saro.saro_urls', name='saro'),
)