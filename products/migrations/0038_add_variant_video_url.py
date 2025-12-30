# Generated migration for adding video_url to ProductVariant

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0037_add_category_specification_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='video_url',
            field=models.URLField(blank=True, help_text='Video URL for this variant (e.g., YouTube, Vimeo)', max_length=500, null=True),
        ),
    ]

