import boto3

from rest_framework import serializers
from rest_auth.serializers import UserDetailsSerializer
import os

print("HEY 1")

class UserSerializer(UserDetailsSerializer):
    occupation = serializers.CharField(min_length=3, max_length=100, source="enterpriseuserprofile.occupation")
    company = serializers.CharField(min_length=3, max_length=100, source="enterpriseuserprofile.company")

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('occupation', 'company', )

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('enterpriseuserprofile', {})

        instance = super(UserSerializer, self).update(instance, validated_data)

        # Get and update user profile.
        if profile_data:
            profile = instance.enterpriseuserprofile

            occupation = profile_data.get('occupation')
            if occupation != None:
                profile.occupation = occupation

            company = profile_data.get('company')
            if company != None:
                profile.company = company

            profile.save()
        return instance

from rest_auth.registration.serializers import RegisterSerializer
from allauth.account import app_settings as allauth_settings
from allauth.utils import email_address_exists
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

class CustomRegisterSerializer(RegisterSerializer):
    print("HEY 2")
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)
    company = serializers.CharField(source="enterpriseuserprofile.company", required=True, min_length=3, max_length=100, write_only=True)
    occupation = serializers.CharField(source="enterpriseuserprofile.occupation", required=True, min_length=3, max_length=100, write_only=True)

    def get_cleaned_data(self):
        profile_data = self.validated_data.pop('enterpriseuserprofile', {})
        return {
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'occupation': profile_data.get('occupation', "N/A"),
            'company': profile_data.get('company', "N/A")
        }

    def save(self, request):
        print("Save called!")
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        setup_user_email(request, user, [])
        user.save()

        profile = user.enterpriseuserprofile
        occupation = self.cleaned_data.get('occupation')
        if occupation != None:
            profile.occupation = occupation

        company = self.cleaned_data.get('company')
        if company != None:
            profile.company = company
        profile.save()
        print("Creating user!", user.id)
        self._createUserData(user.id)
        print("Success!")
        return user

    def _createUserData(self, user_id):
        """Only creates it if doesn't exist already."""
        try:
            access_key = os.environ["ACCESS_KEY_ID"]
            secret_key = os.environ["SECRET_ACCESS_KEY"]
            dynamodb = boto3.resource('dynamodb', region_name='us-west-1', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
            table = dynamodb.Table("UsersDashboardData")
            item = {
                'UserId': user_id,
                'ReposRemaining': 3,
            }
            table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(UserId)"
            )
        except Exception as e:
            print(str(e))
            raise Exception("Error while creating the user dashboard data.")
