from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import random
import logging
from .models import EmailOTP, User
from .utils import send_email_to_client
from .serializer import CreateUserSerializer
from rest_framework.permissions import IsAuthenticated
from .serializer import *
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from django.shortcuts import get_object_or_404


logger = logging.getLogger(__name__)

class EmailRequest(APIView):
    
    def post(self, request):
        email = request.data.get('email')
        try:
            if not email:
                return Response({'message': "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            user=User.objects.filter(email=email)
            if user.exists():
                return Response({'message':'Email is already taken'},status=status.HTTP_226_IM_USED)

            otp = str(random.randint(100000, 999999))
            EmailOTP.objects.update_or_create(email=email, defaults={'otp': otp})
            send_email_to_client(email, otp)

            return Response({'message': f'Email sent to the client {email}'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({'message': "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RegisterUser(APIView):
    parser_classes = [JSONParser,MultiPartParser, FormParser]
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'message': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_record = EmailOTP.objects.filter(email=email).first()
            print(otp_record.otp)

            if not otp_record or otp_record.otp != otp:
                return Response({'message': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = CreateUserSerializer(data=request.data)
            
            if serializer.is_valid():
                serializer.save()
                otp_record.delete()

                return Response({'message': 'User successfully registered'}, status=status.HTTP_201_CREATED)

            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return Response(
                {'message': 'Something went wrong. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class PostCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        serializer=PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, post_id=None):
        if not post_id:
            return Response({"error": "Post ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({"error": "Post not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)

        post.delete()
        return Response({"message": "Post deleted successfully."}, status=status.HTTP_200_OK)


class LikePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):  # changed from 'Like' to 'post'
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'message': 'Post does not exist'}, status=status.HTTP_404_NOT_FOUND)

        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            return Response({'message': 'You already liked this post'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LikeSerializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, post_id):
        try:
            like = Like.objects.get(user=request.user, post_id=post_id)
            like.delete()
            return Response({'message': 'Like removed'}, status=status.HTTP_204_NO_CONTENT)
        except Like.DoesNotExist:
            return Response({'error': 'Like not found'}, status=status.HTTP_404_NOT_FOUND)
        

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'message': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        print(refresh)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        data = request.data.copy()
        data['post'] = post_id
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, post_id):
        comments = Comment.objects.filter(post_id=post_id).order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            to_follow = User.objects.get(id=user_id)
            if to_follow == request.user:
                return Response({'error': "You can't follow yourself"}, status=status.HTTP_400_BAD_REQUEST)

            follow, created = Follow.objects.get_or_create(follower=request.user, following=to_follow)
            if not created:
                return Response({'message': 'Already following this user'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = FollowSerializer(follow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, user_id):
        try:
            to_unfollow = User.objects.get(id=user_id)
            follow = Follow.objects.get(follower=request.user, following=to_unfollow)
            follow.delete()
            return Response({'message': 'Unfollowed successfully'}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Follow.DoesNotExist:
            return Response({'error': 'Not following this user'}, status=status.HTTP_400_BAD_REQUEST)
        
class FeedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        following = Follow.objects.filter(follower=user).values_list('following_id', flat=True)
        posts = Post.objects.filter(user_id__in=following).order_by('-created_at')

        followers_count = Follow.objects.filter(following=user).count()
        following_count = Follow.objects.filter(follower=user).count()

        data = []
        for post in posts:
            data.append({
                'id': post.id,
                'user': {
                    'id': post.user.id,
                    'username': post.user.username,
                },
                'caption': post.caption,
                'image': post.image.url if post.image else '',
                'created_at': post.created_at,
                'followers_count': followers_count,
                'following_count': following_count,
            })

        return Response(data, status=200)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, email):
        user = get_object_or_404(User, email=email)
        posts = Post.objects.filter(user=user).order_by('-created_at')
        print(posts)

        serialized_posts = PostSerializer(posts, many=True, context={'request': request}).data
        followers_count = Follow.objects.filter(following=user).count()
        following_count = Follow.objects.filter(follower=user).count()
        post_count=Post.objects.filter(user=user).count()

        data = {
            'bio': user.bio,
            'username': user.username,
            'profile': request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
            'posts': serialized_posts,
            'followers_count': followers_count,    # <-- add here
            'following_count': following_count,    # <-- add here
            'post_count':post_count
        }

        return Response(data, status=status.HTTP_200_OK)

    

# views.py
class UserDetailUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, email):
        # Ensure user can only update their own data
        if request.user.email != email:
            return Response({'error': 'Not allowed'}, status=403)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        serializer = CreateUserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)


class FollowUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if request.user == target_user:
            return Response({'error': "You can't follow yourself"}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(follower=request.user, following=target_user)

        if not created:
            return Response({'message': 'Already following user'}, status=status.HTTP_403_FORBIDDEN)

        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
class  ExploreProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            followed_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
            users = User.objects.exclude(id__in=followed_ids).exclude(id=request.user.id)
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        

class FollowingListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, email):
        try:
            user = User.objects.get(email=email)
            follow_relations = Follow.objects.filter(follower=user)
            following_users = [relation.following for relation in follow_relations]

            data = [
                {
                    "username": followed_user.username,
                    "email": followed_user.email,
                    "profile": followed_user.profile_image.url if followed_user.profile_image else None,
                    "bio": followed_user.bio,
                }
                for followed_user in following_users
            ]

            return Response(data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        

class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, email):
        try:
            user = User.objects.get(email=email)
            followers_relation = Follow.objects.filter(following=user)
            follower_users = [relation.follower for relation in followers_relation]  # fixed here

            data = [
                {
                    "username": follower_user.username,
                    "email": follower_user.email,
                    "profile": follower_user.profile_image.url if follower_user.profile_image else None,
                    "bio": follower_user.bio,
                }
                for follower_user in follower_users
            ]
            return Response(data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': "User not found"}, status=status.HTTP_404_NOT_FOUND)


class OtherProfileView(APIView):
    permission_classes=[IsAuthenticated]
    

    def get(self, request, email):
        user = get_object_or_404(User, email=email)
        posts = Post.objects.filter(user=user).order_by('-created_at')
        print(posts)

        serialized_posts = PostSerializer(posts, many=True, context={'request': request}).data
        followers_count = Follow.objects.filter(following=user).count()
        following_count = Follow.objects.filter(follower=user).count()

        data = {
            'bio': user.bio,
            'username': user.username,
            'profile': request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
            'posts': serialized_posts,
            'followers_count': followers_count,    # <-- add here
            'following_count': following_count,    # <-- add here
        }

        return Response(data, status=status.HTTP_200_OK)