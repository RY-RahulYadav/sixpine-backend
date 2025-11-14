from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, OTPVerification, PasswordResetToken, ContactQuery, BulkOrder, PaymentPreference, SavedCard, DataRequest, Vendor


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'mobile', 'password', 'password_confirm')
        extra_kwargs = {
            'username': {'required': False},
            'mobile': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
        
        # Auto-generate username from email if not provided
        if not attrs.get('username'):
            attrs['username'] = attrs['email'].split('@')[0]
        
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value
    
    def validate_username(self, value):
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists")
        return value


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = None
            
            # Try to authenticate with email first (since email is our primary identifier)
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                # Try with username if email failed
                user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Must include username and password")


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    interests = serializers.JSONField(default=list, allow_null=False)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'mobile', 'is_verified', 'is_staff', 'is_superuser', 'date_joined', 'interests', 'advertising_enabled', 'whatsapp_enabled', 'whatsapp_order_updates', 'whatsapp_promotional', 'email_promotional')
        read_only_fields = ('id', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
    
    def to_representation(self, instance):
        """Ensure empty lists are returned instead of None"""
        data = super().to_representation(instance)
        # Ensure JSON fields are always arrays, never None
        if data.get('interests') is None:
            data['interests'] = []
        # Ensure boolean fields default to True if None
        if data.get('advertising_enabled') is None:
            data['advertising_enabled'] = True
        if data.get('whatsapp_enabled') is None:
            data['whatsapp_enabled'] = True
        if data.get('whatsapp_order_updates') is None:
            data['whatsapp_order_updates'] = True
        if data.get('whatsapp_promotional') is None:
            data['whatsapp_promotional'] = True
        if data.get('email_promotional') is None:
            data['email_promotional'] = True
        return data


class OTPRequestSerializer(serializers.Serializer):
    """Serializer for requesting OTP"""
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True)
    mobile = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField()
    password_confirm = serializers.CharField()
    otp_method = serializers.ChoiceField(choices=['email', 'whatsapp'])
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        if attrs['otp_method'] == 'whatsapp' and not attrs.get('mobile'):
            raise serializers.ValidationError("Mobile number is required for WhatsApp verification")
        
        return attrs


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value


class OTPResendSerializer(serializers.Serializer):
    """Serializer for resending OTP"""
    email = serializers.EmailField()
    otp_method = serializers.ChoiceField(choices=['email', 'whatsapp'])


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value


class ContactQuerySerializer(serializers.ModelSerializer):
    """Serializer for contact form submissions"""
    class Meta:
        model = ContactQuery
        fields = ['id', 'full_name', 'pincode', 'phone_number', 'email', 'message', 
                  'status', 'admin_notes', 'created_at', 'updated_at', 'resolved_at']
        read_only_fields = ['id', 'status', 'admin_notes', 'created_at', 'updated_at', 'resolved_at']


class ContactQueryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contact queries (user submission)"""
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    message = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = ContactQuery
        fields = ['full_name', 'pincode', 'phone_number', 'email', 'message']
    
    def validate_email(self, value):
        """Convert empty string to None"""
        return value if value else None
    
    def validate_message(self, value):
        """Convert empty string to None"""
        return value if value else None


class BulkOrderSerializer(serializers.ModelSerializer):
    """Serializer for bulk orders"""
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BulkOrder
        fields = ['id', 'company_name', 'contact_person', 'email', 'phone_number', 
                  'address', 'city', 'state', 'pincode', 'country', 'project_type',
                  'estimated_quantity', 'estimated_budget', 'delivery_date',
                  'special_requirements', 'status', 'admin_notes', 'quoted_price',
                  'assigned_to', 'assigned_to_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'admin_notes', 'quoted_price', 'assigned_to', 'created_at', 'updated_at']
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or obj.assigned_to.email
        return None


class BulkOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bulk orders (user submission)"""
    estimated_quantity = serializers.IntegerField(required=False, allow_null=True)
    estimated_budget = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    delivery_date = serializers.DateField(required=False, allow_null=True)
    special_requirements = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    country = serializers.CharField(required=False, default='India')
    
    class Meta:
        model = BulkOrder
        fields = ['company_name', 'contact_person', 'email', 'phone_number', 
                  'address', 'city', 'state', 'pincode', 'country', 'project_type',
                  'estimated_quantity', 'estimated_budget', 'delivery_date',
                  'special_requirements']
    
    def validate_estimated_quantity(self, value):
        """Convert empty string or zero to None"""
        return value if value else None
    
    def validate_estimated_budget(self, value):
        """Convert empty string or zero to None"""
        return value if value else None
    
    def validate_special_requirements(self, value):
        """Convert empty string to None"""
        return value if value else None


class PaymentPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for payment preferences - address is managed via Address table"""
    
    class Meta:
        model = PaymentPreference
        fields = [
            'id', 'preferred_method', 'preferred_card_token_id', 
            'razorpay_customer_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'razorpay_customer_id', 'created_at', 'updated_at']


class SavedCardSerializer(serializers.ModelSerializer):
    """Serializer for saved cards"""
    class Meta:
        model = SavedCard
        fields = [
            'id', 'token_id', 'customer_id', 'card_last4', 'card_network',
            'card_type', 'card_issuer', 'nickname', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DataRequestSerializer(serializers.ModelSerializer):
    """Serializer for data requests"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = DataRequest
        fields = [
            'id', 'user', 'user_email', 'user_name', 'request_type', 'request_type_display',
            'status', 'status_display', 'file_path', 'requested_at', 'approved_at',
            'approved_by', 'approved_by_email', 'completed_at', 'admin_notes'
        ]
        read_only_fields = ['id', 'requested_at', 'approved_at', 'approved_by', 'completed_at', 'file_path']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class DataRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating data requests"""
    class Meta:
        model = DataRequest
        fields = ['request_type']


# ==================== Vendor Serializers ====================

class VendorRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for vendor registration - simplified, business details optional"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField(required=False)
    
    class Meta:
        model = Vendor
        fields = [
            'business_name', 'business_email', 'business_phone', 'business_address',
            'city', 'state', 'pincode', 'country', 'gst_number', 'pan_number',
            'business_type', 'brand_name', 'email', 'first_name', 'last_name',
            'username', 'password', 'password_confirm'
        ]
        extra_kwargs = {
            # Make all business fields optional
            'business_name': {'required': False, 'allow_blank': True},
            'business_email': {'required': False, 'allow_blank': True},
            'business_phone': {'required': False, 'allow_blank': True},
            'business_address': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'state': {'required': False, 'allow_blank': True},
            'pincode': {'required': False, 'allow_blank': True},
            'country': {'required': False, 'allow_blank': True},
            'gst_number': {'required': False, 'allow_blank': True},
            'pan_number': {'required': False, 'allow_blank': True},
            'business_type': {'required': False, 'allow_blank': True},
            'brand_name': {'required': False, 'allow_blank': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate password strength
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})
        
        # Check if user with email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists'})
        
        # Check if vendor with business email already exists (only if provided)
        business_email = attrs.get('business_email')
        if business_email and Vendor.objects.filter(business_email=business_email).exists():
            raise serializers.ValidationError({'business_email': 'A vendor with this business email already exists'})
        
        # Auto-generate username from email if not provided
        if not attrs.get('username'):
            attrs['username'] = attrs['email'].split('@')[0]
        
        # Check if username already exists
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'A user with this username already exists'})
        
        # Set default values for optional business fields if not provided
        if not attrs.get('business_email'):
            attrs['business_email'] = attrs['email']  # Use user email as default
        if not attrs.get('business_name'):
            attrs['business_name'] = f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip() or 'Vendor'
        if not attrs.get('brand_name'):
            attrs['brand_name'] = attrs.get('business_name', 'Vendor')
        if not attrs.get('country'):
            attrs['country'] = 'India'
        
        return attrs
    
    def create(self, validated_data):
        # Extract user fields
        password = validated_data.pop('password')
        password_confirm = validated_data.pop('password_confirm')
        email = validated_data.pop('email')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        username = validated_data.pop('username', email.split('@')[0])
        
        # Create user account
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,  # Vendors have staff access for seller panel
            is_active=True
        )
        
        # Create vendor profile
        vendor = Vendor.objects.create(
            user=user,
            **validated_data
        )
        
        return vendor


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for vendor profile"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'user', 'user_email', 'user_first_name', 'user_last_name',
            'business_name', 'business_email', 'business_phone', 'business_address',
            'city', 'state', 'pincode', 'country', 'gst_number', 'pan_number',
            'business_type', 'brand_name', 'status', 'status_display', 'is_verified',
            'commission_percentage', 'created_at', 'updated_at', 'approved_at', 'approved_by'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'is_verified', 'created_at', 'updated_at',
            'approved_at', 'approved_by', 'commission_percentage'
        ]


class VendorLoginSerializer(serializers.Serializer):
    """Serializer for vendor login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = None
            
            # Try to authenticate with email first
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                # Try with username if email failed
                user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            
            if not user.is_active:
                raise serializers.ValidationError("Account is disabled")
            
            # Check if user has vendor profile
            if not hasattr(user, 'vendor_profile'):
                raise serializers.ValidationError("This account is not registered as a vendor")
            
            vendor = user.vendor_profile
            if not vendor.is_active:
                raise serializers.ValidationError("Vendor account is not active. Please contact support.")
            
            attrs['user'] = user
            attrs['vendor'] = vendor
            return attrs
        else:
            raise serializers.ValidationError("Must include username and password")
