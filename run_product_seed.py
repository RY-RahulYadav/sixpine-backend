#!/usr/bin/env python3
"""
Script to run the product data seed file
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_backend.settings')
django.setup()

from seed_product_data import main

if __name__ == '__main__':
    main()
