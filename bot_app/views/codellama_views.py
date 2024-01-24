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
from ..models import User, SessionDetails, UserQueries, Theme, ImageQueries
from ctransformers import AutoModelForCausalLM
from langchain.llms import CTransformers
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
import threading
import torch


# creates a session store.
session = SessionStore(session_key=settings.SESSION_KEY)
device = "cuda" if torch.cuda.is_available() else "cpu"

# added to load gguf models
codellama = AutoModelForCausalLM.from_pretrained("C:/Users/Stephen Ma/Desktop/Llama-2-Chatbot/", model_file="codellama-34b.Q5_K_M.gguf", model_type="llama")


# Displays the previous queries asked by the user.
def codellamaHomepage(request):
    # print(os.getcwd())
    username = request.session["username"]
    user = User.objects.get(name=username)
    data = UserQueries.objects.filter(user_id=user).values('question_text', 'query_response')
    data = list(data.values())
    print(len(data))
    return render(request, 'codellama.html', {'data': data}) 


# Whenever user clicks requests for a response, the server will send a prompt to the LLM model. And return the response to the html page.
@csrf_exempt
def fetchCode(request):
    print(request.method)
    print(request)
    if request.method == "POST":
        query = QueryForm(request.POST)
        print(query)
        if query.is_valid():
            result = HttpResponse(waitForResult(func=fetchResponseFromCodeLlama, request=request, query=query), content_type='application/json') 
            print(result)
            # return HttpResponse(waitForResult(request=request, query=query), content_type='application/json')  
            return result      


def waitForResult(func, request, query):
    # if multiple user ask question to llama2 this method will wait until the lock has been released.
    # while not lock.acquire():
    #     print("Waiting..")
        # yield JsonResponse({'message':'Generating response'})

    # Once lock is released, the user's query will be sent to the llama2 model.
    try:
        query = func(request, query)
    except Exception as error:
        print("Failed to get response",type(error).__name__, "–", error)
        # yield JsonResponse({'message':'Failed to get response. Kindly re-enter your query..'})
    # finally:
        # lock.release()

    return query


# fetches the query response from llama 2 model and saves the respective user's queries in the database.
def fetchResponseFromCodeLlama(request, query):
    query_text = query.cleaned_data["query"]
    print(query_text)
    prompt = "Q: " + query_text + "? A:"
    output = codellama(prompt) # fetches the response from the model
    response = output
    user: User = User.objects.get(name=request.session["username"]) 
    queries = UserQueries(question_text=query_text, query_response=response, user_id=user,
                                timestamp=timezone.now())
    queries.save()              # saves the query and response into database.
    query_resp = {
        'question_text':queries.question_text,
        'query_response':response
    }
    return JsonResponse(query_resp)