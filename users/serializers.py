from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username']
        read_only_fields = ['id', 'email', 'username']


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
    )
    username = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_email

    def validate_username(self, value):
        if value:
            username = value.strip()
            if User.objects.filter(username__iexact=username).exists():
                raise serializers.ValidationError("A user with this username already exists.")
            return username
        return value

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']
        username = validated_data.get('username') or email

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password', '')

        user = User.objects.filter(email__iexact=email).first()

        # Generic authentication failure message to prevent account enumeration
        if user is None or not user.check_password(password) or not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")

        attrs['user'] = user
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=False, allow_blank=False)
    access_token = serializers.CharField(required=False, allow_blank=False)
    code = serializers.CharField(required=False, allow_blank=False)
    redirect_uri = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        if not any([attrs.get('id_token'), attrs.get('access_token'), attrs.get('code')]):
            raise serializers.ValidationError(
                "Either id_token, access_token, or code must be provided."
            )
        return attrs
