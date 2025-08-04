from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'www', 'main_app.urls', name='www'),
    host(r'webhook', 'automate.webhook_urls', name='webhook'),
    host(r'taro', 'taro.taro_urls', name='taro'),
)