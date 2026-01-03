from django.core.management.base import BaseCommand
from django.db.models import Q
from products.models import (
    CategorySpecificationTemplate, VariantStyleSpec, VariantMeasurementSpec,
    VariantFeature, VariantUserGuide, VariantItemDetail, ProductVariant,
    ProductSpecification
)


class Command(BaseCommand):
    help = 'Fix sort_order for all variant specifications based on CategorySpecificationTemplate'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to fix sort_order for all specifications...'))
        
        # Get all variants
        variants = ProductVariant.objects.all()
        total_variants = variants.count()
        
        self.stdout.write(f'Processing {total_variants} variants...')
        
        updated_counts = {
            'specifications': 0,
            'style_specs': 0,
            'measurement_specs': 0,
            'features': 0,
            'user_guide': 0,
            'item_details': 0
        }
        
        for idx, variant in enumerate(variants, 1):
            if idx % 10 == 0:
                self.stdout.write(f'Processing variant {idx}/{total_variants}...')
            
            # Get the category
            category = variant.product.category
            if not category:
                continue
            
            # Fix specifications (Key Details)
            specifications = variant.specifications.all()
            for spec in specifications:
                template = CategorySpecificationTemplate.objects.filter(
                    category=category,
                    section='specifications',
                    field_name__iexact=spec.name,
                    is_active=True
                ).first()
                
                if template and spec.sort_order != template.sort_order:
                    spec.sort_order = template.sort_order
                    spec.save(update_fields=['sort_order'])
                    updated_counts['specifications'] += 1
            
            # Fix style specs
            style_specs = variant.style_specs.all()
            for spec in style_specs:
                template = CategorySpecificationTemplate.objects.filter(
                    category=category,
                    section='style_specs',
                    field_name__iexact=spec.name,
                    is_active=True
                ).first()
                
                if template and spec.sort_order != template.sort_order:
                    spec.sort_order = template.sort_order
                    spec.save(update_fields=['sort_order'])
                    updated_counts['style_specs'] += 1
            
            # Fix measurement specs
            measurement_specs = variant.measurement_specs.all()
            for spec in measurement_specs:
                template = CategorySpecificationTemplate.objects.filter(
                    category=category,
                    section='measurement_specs',
                    field_name__iexact=spec.name,
                    is_active=True
                ).first()
                
                if template and spec.sort_order != template.sort_order:
                    spec.sort_order = template.sort_order
                    spec.save(update_fields=['sort_order'])
                    updated_counts['measurement_specs'] += 1
            
            # Fix features
            features = variant.features.all()
            for feature in features:
                template = CategorySpecificationTemplate.objects.filter(
                    category=category,
                    section='features',
                    field_name__iexact=feature.name,
                    is_active=True
                ).first()
                
                if template and feature.sort_order != template.sort_order:
                    feature.sort_order = template.sort_order
                    feature.save(update_fields=['sort_order'])
                    updated_counts['features'] += 1
            
            # Fix user guide
            user_guides = variant.user_guide.all()
            for guide in user_guides:
                template = CategorySpecificationTemplate.objects.filter(
                    category=category,
                    section='user_guide',
                    field_name__iexact=guide.name,
                    is_active=True
                ).first()
                
                if template and guide.sort_order != template.sort_order:
                    guide.sort_order = template.sort_order
                    guide.save(update_fields=['sort_order'])
                    updated_counts['user_guide'] += 1
            
            # Fix item details
            item_details = variant.item_details.all()
            for detail in item_details:
                template = CategorySpecificationTemplate.objects.filter(
                    category=category,
                    section='item_details',
                    field_name__iexact=detail.name,
                    is_active=True
                ).first()
                
                if template and detail.sort_order != template.sort_order:
                    detail.sort_order = template.sort_order
                    detail.save(update_fields=['sort_order'])
                    updated_counts['item_details'] += 1
        
        self.stdout.write(self.style.SUCCESS('\nUpdate Summary:'))
        self.stdout.write(f'Specifications (Key Details) updated: {updated_counts["specifications"]}')
        self.stdout.write(f'Style Specs updated: {updated_counts["style_specs"]}')
        self.stdout.write(f'Measurement Specs updated: {updated_counts["measurement_specs"]}')
        self.stdout.write(f'Features updated: {updated_counts["features"]}')
        self.stdout.write(f'User Guides updated: {updated_counts["user_guide"]}')
        self.stdout.write(f'Item Details updated: {updated_counts["item_details"]}')
        self.stdout.write(self.style.SUCCESS('\nSuccessfully fixed all sort_order values!'))
