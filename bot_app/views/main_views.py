#django imports
from django.shortcuts import render, redirect
from django.contrib.sessions.backends.file import SessionStore
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# custom imports
from ..forms import QueryForm, SignInForm, SignUpForm, ThemeForm, ImageForm
from django.contrib import messages
# from llama_cpp import Llama
from ..models import User, SessionDetails, UserQueries, Theme, ImageQueries, CodeQueries, ChatHistories
from ctransformers import AutoModelForCausalLM
from langchain.llms import CTransformers
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import threading
import uuid
from datetime import datetime, timedelta, timezone 
# from .llama_views import llamaHomepage

# # clip imports 
# import torch
# import clip
# from ..clip import build_embeddings, build_index, search
# from django.core.files import File
# from django.core.files.uploadedfile import InMemoryUploadedFile
# from django.core.files.base import ContentFile
# from io import BytesIO

import os

# creates a session store. 
session = SessionStore(session_key=settings.SESSION_KEY) 

# default home page (Llama 2) 
def llamaHomepage(request):
    username = request.session["username"]
    user = User.objects.get(name=username) 

    chatHistories = ChatHistories.objects.filter(user_id=user, model="Llama 2").values('chathistory_id', 'chathistory_title', 'starred', 'timestamp') 
    chatHistories = list(chatHistories.values()) 
    data = categorize_dates(chatHistories) 
    # data = list(data.values())

    for category, items in data.items():
        if items:
            print(f"{category}:")
            for item in items:
                print(item) 
    return render(request, 'index.html', {'data': data, 'username': username}) 

@csrf_exempt
def updateTheme(request):
    username = request.session["username"]
    user = User.objects.get(name=username)
    theme = request.POST.get('theme')
    user_preference, created = Theme.objects.get_or_create(user_id=user)
    user_preference.theme = theme
    print(theme)
    user_preference.save()
    return JsonResponse({'success': True}) 

@csrf_exempt
def getTheme(request): 
    username = request.session["username"]
    user = User.objects.get(name=username)
    user_preference, created = Theme.objects.get_or_create(user_id=user)
    theme = user_preference.theme
    return JsonResponse({'theme': theme})

@csrf_exempt
def deleteChats(request):
    username = request.session["username"]
    user = User.objects.get(name=username)

    chatHistory = request.POST.get("chathistory_id")
    model_name = request.POST.get("model_name")
    print(chatHistory)
    chathistory_id: ChatHistories = ChatHistories.objects.get(user_id=user, chathistory_id=chatHistory)
    print(chathistory_id)
    if (model_name == "Llama 2"): 
        ChatHistories.objects.filter(user_id=user, chathistory_id=chatHistory).delete() 
        UserQueries.objects.filter(chathistory_id=chathistory_id).delete() 
    elif (model_name == "Code Llama"): 
        ChatHistories.objects.filter(user_id=user, chathistory_id=chatHistory).delete() 
        CodeQueries.objects.filter(chathistory_id=chathistory_id).delete() 
    else: 
        ChatHistories.objects.filter(user_id=user, chathistory_id=chatHistory).delete() 
        ImageQueries.objects.filter(chathistory_id=chathistory_id).delete() 
    return JsonResponse({'message': 'History cleared successfully'}) 


# signin 
def signin(request):
    if request.method == "POST": 
        sign_in_details = SignInForm(request.POST)
        if sign_in_details.is_valid():
            username = sign_in_details.cleaned_data["username"]
            password = sign_in_details.cleaned_data["password"]
            try:
                user: User = User.objects.get(name=username)
                if password == user.password:
                    createsession(request, user, username)
                    return redirect(llamaHomepage)
                else:
                    messages.warning(request, 'Incorrect Password')
            except:
                messages.warning(request, 'User ID not found. Please register...')
    return render(request, 'login.html')

# login auto-creates a new session 
def createsession(request, user, username):
    session["username"] = username
    session.create()
    request.session = session
    session_details = SessionDetails(user_id=user, session_id=session.session_key)
    session_details.save() 

# signup 
def signup(request):
    if request.method == "POST":
        signup_details = SignUpForm(request.POST)
        if signup_details.is_valid():
            username = signup_details.cleaned_data["username"]
            password = signup_details.cleaned_data["password"]
            user = User(name=username, password=password, role='user')
            user.save()
            createsession(request=request, user=user, username=username)
            return redirect(llamaHomepage)

    return render(request, 'signup.html') 

# fetch chat history data 
@csrf_exempt
def fetchChatHistory(request): 
    username = request.session["username"]
    user = User.objects.get(name=username)

    chatHistory = request.POST.get("chathistory_id")
    model_name = request.POST.get("model_name") 

    chathistory_id: ChatHistories = ChatHistories.objects.get(user_id=user, chathistory_id=chatHistory) 

    # update session 
    session["chathistory_id"] = chatHistory
    session.save()
    request.session["chathistory_id"] = chatHistory
    print(request.session["chathistory_id"]) 

    # retrieve data 
    data = None
    if (model_name == "Llama 2"): 
        data = UserQueries.objects.filter(chathistory_id=chathistory_id).values('question_text', 'query_response')
    elif (model_name == "Code Llama"): 
        data = CodeQueries.objects.filter(chathistory_id=chathistory_id).values('question_text', 'query_response')
    else: 
        data = ImageQueries.objects.filter(chathistory_id=chathistory_id).values('question_text', 'image', 'image_response') 
    data = list(data.values())
    for item in data: 
        print(item)
    return JsonResponse(data, safe=False) 

# update starred status of chat history data 
@csrf_exempt
def updateStarred(request): 
    username = request.session["username"]
    user = User.objects.get(name=username)

    chatHistory = request.POST.get("chathistory_id") 
    chatHistory = ChatHistories.objects.get(user_id=user, chathistory_id=chatHistory) 
    chatHistory.starred = request.POST.get("starred") 
    chatHistory.save() 
    return JsonResponse({'success': True}) 

# categorize datetimes for side bar window 
def categorize_dates(data): 
    # Sort data by datetime in descending order 
    data.sort(key=lambda x: x['timestamp'], reverse=True)
    today = datetime.now(timezone.utc)
    yesterday = today - timedelta(days=1)
    previous_7_days = today - timedelta(days=7)
    previous_30_days = today - timedelta(days=30)

    categorized_data = {
        'Today': [],
        'Yesterday': [],
        'Previous 7 Days': [],
        'Previous 30 Days': [],
    }

    for item in data:
        item_date = item['timestamp']

        if item_date.date() == today.date():
            categorized_data['Today'].append(item)
        elif item_date.date() == yesterday.date():
            categorized_data['Yesterday'].append(item)
        elif item_date >= previous_7_days:
            categorized_data['Previous 7 Days'].append(item)
        elif item_date >= previous_30_days:
            categorized_data['Previous 30 Days'].append(item)

    return categorized_data 

# # generate unique id for chat history 
# def generate_unique_id(model_name): 
#     check = False; 
#     unique_id; 

#     while (not check): 
#         # generate a unique ID (UUID)
#         unique_id = uuid.uuid4()

#         # convert the UUID to a string if needed
#         unique_id = str(unique_id) 

#         # check uniqueness 
#         username = session["username"]
#         user = User.objects.get(name=username)        
#         if (model_name == "Llama 2"): 
#             check = UserQueries.objects.filter(user_id=user).exists()
#         elif (model_name == "Code Llama"): 
#             check = CodeQueries.objects.filter(user_id=user).exists() 
#         else: 
#             check = ImageQueries.objects.filter(user_id=user).exists()
#     return unique_id