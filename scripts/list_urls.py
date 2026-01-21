import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    import django
    django.setup()
    from django.urls import get_resolver

    resolver = get_resolver()

    def walk(patterns, prefix=''):
        for p in patterns:
            if hasattr(p, 'url_patterns'):
                walk(p.url_patterns, prefix + str(p.pattern))
            else:
                print(f"{p.name or '-'}\t {prefix}{p.pattern}")

    if __name__ == '__main__':
        walk(resolver.url_patterns)
except Exception:
    print('Error while loading Django or URLConf:', file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
