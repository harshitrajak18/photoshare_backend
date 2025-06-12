"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from otp_verification import views
from django.conf import settings
from django.conf.urls.static import static
from otp_verification.views import (
    EmailRequest,
    RegisterUser,
    LoginView,
    PostCreateView,
    LikePostView,
    CommentCreateView,
    FollowUserView,
    FeedView,
    ProfileView,
    UserDetailUpdateView,
    ExploreProfileView,
    FollowingListView,
    FollowersListView,
    OtherProfileView
    
    )


urlpatterns = [
    # Email OTP & Registration
    path('email-request/', EmailRequest.as_view(), name='email-request'),

    path('register/', RegisterUser.as_view(), name='register'),

    path('login/', LoginView.as_view(), name='login'),

    # Post creation
    path('create-post/', PostCreateView.as_view(), name='create-post'),

    # Like/Unlike Post
    path('posts/<int:post_id>/like/', LikePostView.as_view(), name='like-post'),

    # Comment on Post
    path('posts/<int:post_id>/comments/', CommentCreateView.as_view(), name='comments'),

    # Follow/Unfollow User
    path('users/<str:username>/', FollowUserView.as_view(), name='follow-user'),

    path('feed/', FeedView.as_view(), name='feed'),

    path('profile/<str:email>/', ProfileView.as_view(), name='Profile'),

    path('like-post/<int:post_id>/', LikePostView.as_view(), name='like-post'),

    path('delete-post/<int:post_id>/',PostCreateView.as_view(),name='delete-post'),

    path('update_user/<str:email>',UserDetailUpdateView.as_view(),name='update-profile'),

    path('explore',ExploreProfileView.as_view(),name='explore'),

    path('following/<str:email>',FollowingListView.as_view(),name='following-list'),

    path('followers/<str:email>',FollowersListView.as_view(),name='followers-list'),

    path('other-profiles/<str:email>',OtherProfileView.as_view(),name='other-profile')

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
